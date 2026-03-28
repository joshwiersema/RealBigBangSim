# Architecture Research

**Domain:** Real-time cosmological simulation visualization (GPU-accelerated particle system)
**Researched:** 2026-03-27
**Confidence:** HIGH (core rendering pipeline patterns are well-established; cosmological-specific layering is MEDIUM)

## Standard Architecture

### System Overview

```
+===================================================================+
|                      APPLICATION LAYER                            |
|  +-------------+  +--------------+  +---------------------------+ |
|  | Window /    |  | Input        |  | Application State Machine | |
|  | Event Loop  |  | Handler      |  | (Era transitions, time)   | |
|  +------+------+  +------+-------+  +-------------+-------------+ |
|         |                |                        |               |
+=========|================|========================|===============+
|         v                v                        v               |
|                    SIMULATION LAYER                               |
|  +------------------+  +------------------+  +------------------+ |
|  | Physics Engine   |  | Era Manager      |  | Timeline         | |
|  | (Friedmann eqs,  |  | (state machine,  |  | Controller       | |
|  |  Saha, Jeans)    |  |  era configs)    |  | (time mapping)   | |
|  +--------+---------+  +--------+---------+  +--------+---------+ |
|           |                     |                     |           |
+===========|=====================|=====================|===========+
|           v                     v                     v           |
|                     RENDERING LAYER                               |
|  +------------------+  +------------------+  +------------------+ |
|  | Particle System  |  | Shader Manager   |  | Camera System    | |
|  | (GPU buffers,    |  | (per-era GLSL,   |  | (cinematic +     | |
|  |  compute update) |  |  post-processing)|  |  manual orbit)   | |
|  +--------+---------+  +--------+---------+  +--------+---------+ |
|           |                     |                     |           |
|           v                     v                     v           |
|  +------------------+  +------------------+                       |
|  | Framebuffer      |  | Post-Processing  |                       |
|  | Pipeline (FBO    |  | Chain (bloom,    |                       |
|  |  render targets) |  |  tone mapping)   |                       |
|  +--------+---------+  +--------+---------+                       |
|           |                     |                                 |
+===========|=====================|=================================+
|           v                     v                                 |
|                     PRESENTATION LAYER                            |
|  +------------------+  +------------------+  +------------------+ |
|  | HUD / Overlay    |  | Audio Engine     |  | Capture System   | |
|  | (ImGui or custom |  | (sounddevice     |  | (screenshot,     | |
|  |  text rendering) |  |  callback thread)|  |  video recording)|
|  +------------------+  +------------------+  +------------------+ |
+===================================================================+
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Window / Event Loop** | Creates OpenGL context, runs main loop, dispatches events | `moderngl-window` WindowConfig subclass with `on_render(time, frametime)` |
| **Input Handler** | Translates mouse/keyboard into camera commands and UI actions | Event callbacks from moderngl-window, mapped to camera/state actions |
| **Application State Machine** | Manages simulation state (paused, running, transitioning) and era progression | Simple enum-based FSM; no library needed for ~11 states |
| **Physics Engine** | Computes cosmological parameters per timestep (scale factor, temperature, density) | Pure Python module using NumPy; feeds uniforms to shaders each frame |
| **Era Manager** | Defines era boundaries, visual configs, transition blending, per-era shader params | Data-driven configs (dataclass or dict per era) with interpolation at boundaries |
| **Timeline Controller** | Maps wall-clock time to cosmic time (logarithmic mapping across 13.8 Gyr) | Logarithmic time remapping function; controls simulation speed |
| **Particle System** | Manages GPU particle buffers (positions, velocities, properties), dispatches compute shaders | ModernGL SSBOs with ping-pong double buffering; compute shader dispatch |
| **Shader Manager** | Loads, compiles, caches GLSL programs; manages per-era shader switching | Dictionary of compiled Programs keyed by purpose (compute, render, post-process) |
| **Camera System** | Cinematic auto-camera with keyframed paths; manual orbit/zoom/pan override | Spherical coordinates (azimuth, elevation, radius) with lerp interpolation |
| **Framebuffer Pipeline** | Off-screen render targets for multi-pass rendering | ModernGL Framebuffer with HDR color attachment (RGBA16F texture) |
| **Post-Processing Chain** | Bloom, tone mapping, vignette applied after main render | Sequence of full-screen quad passes reading/writing between FBOs |
| **HUD / Overlay** | Educational text, era labels, temperature/density readouts, milestone markers | ImGui via pyimgui + moderngl-window integration, or custom bitmap font rendering |
| **Audio Engine** | Generates ambient soundscape tied to physics parameters | sounddevice OutputStream with callback; parameters fed via thread-safe queue |
| **Capture System** | Screenshot (read framebuffer to PNG) and video recording (ffmpeg pipe) | `framebuffer.read()` to PIL/Pillow for screenshots; ffmpeg subprocess for video |

## Recommended Project Structure

```
bigbangsim/
├── __main__.py              # Entry point: create window, run loop
├── app.py                   # WindowConfig subclass, main loop orchestration
├── config.py                # Global constants, performance settings
│
├── simulation/              # Pure physics, no rendering
│   ├── __init__.py
│   ├── cosmology.py         # Friedmann equations, scale factor, Hubble parameter
│   ├── timeline.py          # Cosmic time <-> wall-clock time mapping
│   ├── eras.py              # Era definitions, boundaries, parameters
│   └── physics/             # Per-era physics models
│       ├── __init__.py
│       ├── nucleosynthesis.py
│       ├── recombination.py
│       └── structure.py
│
├── rendering/               # All GPU / ModernGL code
│   ├── __init__.py
│   ├── particles.py         # Particle system (buffers, compute dispatch)
│   ├── shaders.py           # Shader loading, compilation, caching
│   ├── camera.py            # Camera system (cinematic + manual)
│   ├── framebuffers.py      # FBO management, render target setup
│   ├── postprocessing.py    # Bloom, tone mapping, vignette
│   └── background.py        # Background rendering (CMB, void, starfield)
│
├── shaders/                 # GLSL source files
│   ├── compute/
│   │   ├── particle_update.glsl
│   │   └── structure_formation.glsl
│   ├── vertex/
│   │   ├── particle.vert
│   │   └── fullscreen_quad.vert
│   ├── fragment/
│   │   ├── particle_plasma.frag
│   │   ├── particle_matter.frag
│   │   ├── particle_stars.frag
│   │   ├── bloom_bright.frag
│   │   ├── bloom_blur.frag
│   │   ├── tonemap.frag
│   │   └── background.frag
│   └── include/
│       ├── colormap.glsl     # Shared color mapping utilities
│       └── noise.glsl        # Shared noise functions
│
├── audio/                   # Sound generation
│   ├── __init__.py
│   ├── engine.py            # Audio engine (sounddevice stream management)
│   ├── generators.py        # Oscillators, noise, drone generators
│   └── parameters.py        # Physics-to-audio parameter mapping
│
├── ui/                      # HUD and overlays
│   ├── __init__.py
│   ├── hud.py               # Main HUD rendering
│   ├── labels.py            # Era labels, milestone markers
│   └── readouts.py          # Temperature, density, time displays
│
├── capture/                 # Screenshot and video
│   ├── __init__.py
│   ├── screenshot.py        # Single frame capture
│   └── recorder.py          # Video recording (ffmpeg pipe)
│
├── data/                    # Static data files
│   ├── cosmological_params.py  # Planck 2018 values, PDG constants
│   ├── era_configs.json     # Era visual/audio configurations
│   └── camera_paths.json    # Cinematic camera keyframes per era
│
└── tests/
    ├── test_cosmology.py
    ├── test_timeline.py
    └── test_eras.py
```

### Structure Rationale

- **simulation/ vs rendering/:** Strict separation. Physics computes numbers (temperature, density, scale factor). Rendering consumes those numbers as shader uniforms. This allows testing physics without a GPU context, and swapping visual styles without touching physics.
- **shaders/ as flat files:** GLSL files are separate from Python code because they are compiled at runtime by the GPU driver. Keeping them in a dedicated tree makes shader development (edit, reload, iterate) fast. The `include/` subfolder holds shared GLSL snippets.
- **audio/ as independent module:** Audio runs on its own thread (sounddevice callback). It receives physics parameters through a thread-safe interface but has zero coupling to the rendering layer. This prevents audio glitches from frame drops.
- **data/ for configuration:** Era definitions, camera paths, and cosmological constants live in data files (JSON or Python dataclasses). This makes the simulation tunable without code changes, and keeps scientific constants auditable.

## Architectural Patterns

### Pattern 1: Fixed-Timestep Simulation with Variable Render Rate

**What:** The physics simulation advances in fixed time steps (e.g., every 16ms of simulation time), decoupled from the rendering frame rate. The render loop runs as fast as it can and interpolates between physics states for smooth visuals.

**When to use:** Always. This is the standard pattern for any real-time simulation. Physics stability requires fixed timesteps; visual smoothness requires rendering at the monitor's refresh rate.

**Trade-offs:** Adds complexity (accumulator pattern, interpolation state) but prevents physics explosions at low framerates and provides consistent behavior across hardware.

**Example:**
```python
class App(WindowConfig):
    PHYSICS_DT = 1.0 / 60.0  # Fixed physics timestep

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accumulator = 0.0
        self.sim_state = SimulationState()
        self.prev_state = SimulationState()

    def on_render(self, time: float, frametime: float):
        self.accumulator += frametime

        while self.accumulator >= self.PHYSICS_DT:
            self.prev_state = self.sim_state.copy()
            self.sim_state.step(self.PHYSICS_DT)
            self.accumulator -= self.PHYSICS_DT

        alpha = self.accumulator / self.PHYSICS_DT
        render_state = self.prev_state.lerp(self.sim_state, alpha)

        self.renderer.draw(render_state)
```

### Pattern 2: Ping-Pong Double Buffering for GPU Particle Updates

**What:** Two SSBOs (Shader Storage Buffer Objects) alternate roles each frame: one is read-only input, the other is write-only output. After the compute shader runs, they swap. This avoids read-write hazards on the GPU.

**When to use:** Any time a compute shader needs to read the current state of all particles and write updated state. Required because OpenGL does not allow reading and writing the same buffer location simultaneously.

**Trade-offs:** Doubles GPU memory for particle buffers (2x positions, 2x velocities). For 1M particles with vec4 position + vec4 velocity, that is ~32MB -- trivial for any modern GPU.

**Example:**
```python
class ParticleSystem:
    def __init__(self, ctx, count):
        self.count = count
        # Two position buffers for ping-pong
        self.pos_buffers = [
            ctx.buffer(reserve=count * 16),  # vec4 per particle
            ctx.buffer(reserve=count * 16),
        ]
        self.vel_buffer = ctx.buffer(reserve=count * 16)
        self.current = 0  # Index of "read" buffer

    def update(self, compute_shader, dt):
        read_buf = self.pos_buffers[self.current]
        write_buf = self.pos_buffers[1 - self.current]

        read_buf.bind_to_storage_buffer(0)   # layout(binding=0) readonly
        write_buf.bind_to_storage_buffer(1)  # layout(binding=1) writeonly
        self.vel_buffer.bind_to_storage_buffer(2)

        compute_shader['dt'].value = dt
        compute_shader.run(group_x=self.count // 256)

        self.current = 1 - self.current  # Swap

    def get_render_buffer(self):
        return self.pos_buffers[self.current]
```

### Pattern 3: Data-Driven Era Configuration

**What:** Each cosmological era is defined as a data record (not code) containing: time boundaries, physics parameters, visual settings (shader variant, color palette, particle appearance), audio parameters, camera path reference, and HUD text. The Era Manager interpolates between adjacent era configs during transitions.

**When to use:** When you have 11+ distinct visual/behavioral phases with smooth transitions between them. Hard-coding era logic creates unmaintainable switch statements.

**Trade-offs:** Requires a well-designed schema upfront. But once built, adding or tuning eras is purely data editing. Transitions become trivial (lerp between two config snapshots).

**Example:**
```python
@dataclass
class EraConfig:
    name: str
    start_time: float          # Cosmic time (seconds after Big Bang)
    end_time: float
    temperature_range: tuple   # (start_K, end_K)
    particle_shader: str       # Which fragment shader to use
    particle_size: float
    bloom_intensity: float
    color_palette: str         # Reference to colormap
    audio_profile: str         # Reference to audio generator config
    camera_path: str           # Reference to camera keyframes
    hud_description: str

ERAS = [
    EraConfig(
        name="Quark-Gluon Plasma",
        start_time=1e-12,
        end_time=1e-6,
        temperature_range=(1e15, 1e12),
        particle_shader="particle_plasma",
        particle_size=4.0,
        bloom_intensity=0.8,
        color_palette="plasma_hot",
        audio_profile="high_energy_drone",
        camera_path="tight_zoom",
        hud_description="Quarks and gluons form a superhot plasma..."
    ),
    # ... more eras
]
```

### Pattern 4: Multi-Pass Framebuffer Rendering Pipeline

**What:** Instead of rendering directly to the screen, the scene is rendered to an off-screen HDR framebuffer. Then a chain of post-processing passes (bloom extraction, Gaussian blur, tone mapping, compositing) transform the image before final display.

**When to use:** Any time you need bloom, glow, HDR, or per-pixel effects. Essential for this project since particle glow (especially in plasma/radiation eras) requires bloom, and the visual style demands HDR.

**Trade-offs:** Each pass is a full-screen quad draw, adding GPU cost proportional to resolution. For a 1920x1080 target, 4-5 passes add roughly 1-2ms per frame on a GTX 1060 -- well within budget.

**Pipeline:**
```
Pass 1: Scene render (particles + background) -> HDR FBO (RGBA16F)
Pass 2: Bright-pass extraction -> Bloom FBO (half-res)
Pass 3: Horizontal Gaussian blur -> Blur FBO A
Pass 4: Vertical Gaussian blur -> Blur FBO B
Pass 5: Composite (scene + bloom) + tone mapping -> Screen
Pass 6: HUD overlay (ImGui or custom) -> Screen (alpha blended)
```

## Data Flow

### Main Loop Data Flow

```
[Wall Clock Time]
       |
       v
[Timeline Controller] -- maps to --> [Cosmic Time (seconds after Big Bang)]
       |
       v
[Era Manager] -- looks up --> [Current Era Config + Next Era Config + blend factor]
       |
       +---> [Physics Engine]
       |         |
       |         +--> scale_factor, temperature, density, Hubble_param
       |         |    (computed from Friedmann equations + era-specific models)
       |         |
       |         v
       |    [Shader Uniforms]  -----> [Compute Shader: particle update]
       |         |                          |
       |         |                          v
       |         |                    [Particle SSBOs (ping-pong)]
       |         |                          |
       |         v                          v
       |    [Render Shader] <--------- [Vertex Array reads positions]
       |         |
       |         v
       |    [HDR Framebuffer]
       |         |
       |         v
       |    [Post-Processing Chain] --> [Screen Framebuffer]
       |
       +---> [Camera System] -- view/projection matrices --> [Render Shader uniforms]
       |
       +---> [Audio Engine] -- physics params via queue --> [sounddevice callback thread]
       |
       +---> [HUD System] -- era info, readouts --> [ImGui overlay on screen]
```

### Per-Frame Execution Order

```
1. Calculate frametime (delta from last frame)
2. Accumulate physics timesteps
   a. For each fixed step: advance cosmic time, recompute physics params
   b. Update era state (current era, transition blend)
3. Upload uniforms to GPU (temperature, density, scale_factor, dt, era_blend)
4. Dispatch compute shader (particle positions/velocities update)
5. Memory barrier (ensure compute writes visible to vertex shader)
6. Update camera (cinematic interpolation or manual input)
7. Set view/projection matrix uniforms
8. Bind HDR framebuffer
9. Clear + render particles (instanced points or sprites)
10. Render background (if applicable for current era)
11. Post-processing passes (bloom, blur, tone map, composite)
12. Render HUD overlay to screen
13. Swap buffers (presents frame, polls input events)
14. Push physics state to audio queue (non-blocking)
```

### Key Data Flows

1. **Physics-to-GPU flow:** Physics engine computes scalar values (temperature, density, scale factor) each timestep. These become uniform values on the compute shader (controlling particle behavior) and fragment shader (controlling visual appearance like color mapping). This is the critical path -- uniforms are cheap (a few floats per frame).

2. **Particle buffer flow:** Particle data lives entirely on the GPU after initial upload. The compute shader reads from buffer A, writes to buffer B, then they swap. The vertex shader reads from the "current" buffer to render. No CPU readback is needed during normal operation -- data stays GPU-side.

3. **Audio parameter flow:** Physics parameters (temperature, density, expansion rate) are pushed to a thread-safe queue once per physics step. The sounddevice callback thread pops the latest values and uses them to modulate oscillator frequencies, amplitudes, and filter cutoffs. This is deliberately lossy -- audio only needs approximate current state, not every physics step.

4. **Camera flow:** The camera system produces a 4x4 view matrix and 4x4 projection matrix each frame. These are uploaded as uniforms. In cinematic mode, the camera interpolates along keyframed paths defined per-era. In manual mode, mouse input updates spherical coordinates directly.

## Scaling Considerations

| Concern | At 100K particles | At 500K particles | At 1M particles |
|---------|-------------------|--------------------|--------------------|
| **GPU memory** | ~6 MB (trivial) | ~32 MB (trivial) | ~64 MB (fine on GTX 1060 with 6GB) |
| **Compute shader** | <0.5ms per dispatch | ~1-2ms per dispatch | ~2-4ms per dispatch |
| **Vertex rendering** | <1ms (instanced points) | ~2-3ms | ~4-6ms (may need LOD) |
| **Post-processing** | Resolution-dependent, not particle-dependent | Same | Same |
| **CPU physics** | Negligible (uniform computation, not per-particle) | Same | Same |

### Scaling Priorities

1. **First bottleneck: Fragment overdraw from particles.** When many particles overlap (dense plasma eras), fragment shaders fire millions of times. Mitigation: use additive blending (single pass, no sorting), reduce particle size in dense regions, or use compute-based accumulation instead of rasterization for the densest eras.

2. **Second bottleneck: Compute shader dispatch time at 1M particles.** If physics per-particle gets complex (e.g., neighbor interactions for structure formation), compute time grows. Mitigation: keep per-particle compute simple (position += velocity * dt + forces), use spatial hashing only if neighbor queries are truly needed (likely not -- use statistical approximations per the project constraints).

3. **Third bottleneck: Post-processing at high resolution.** Bloom with large kernel at 4K resolution can cost 3-5ms. Mitigation: run bloom at half or quarter resolution (standard practice, visually indistinguishable for glow effects).

## Anti-Patterns

### Anti-Pattern 1: CPU-Side Particle Updates

**What people do:** Update particle positions in Python/NumPy on the CPU, then upload to GPU every frame.
**Why it's wrong:** For 1M particles, this means transferring ~16MB per frame across the PCIe bus. At 60 FPS that is ~1 GB/s of CPU-GPU transfer, which will destroy frame rate. NumPy loops over 1M elements are also slow (even vectorized, ~5-10ms vs <1ms on GPU).
**Do this instead:** Initialize particle buffers on GPU once. Use compute shaders for all per-particle updates. Data stays GPU-resident. CPU only uploads a handful of uniform values per frame (temperature, dt, forces -- maybe 100 bytes total).

### Anti-Pattern 2: One Monolithic Shader for All Eras

**What people do:** Write a single fragment shader with `if (era == PLASMA) { ... } else if (era == MATTER) { ... }` branches for all 11 eras.
**Why it's wrong:** GPU shader execution is SIMD -- all threads in a warp execute the same branch. Divergent branches kill parallelism. A shader with 11 branches compiles to enormous code that thrashes the instruction cache. Also unmaintainable.
**Do this instead:** Compile separate fragment shader programs per visual style (plasma, matter, stars, galaxies). Switch programs when the era changes. During transitions, render to two FBOs with different shaders and alpha-blend the results. Program switching is cheap (a few microseconds) when done once per frame at era boundaries.

### Anti-Pattern 3: Blocking Audio Generation in the Render Loop

**What people do:** Generate audio samples synchronously in the render loop, or block the render loop waiting for audio operations.
**Why it's wrong:** Audio generation must be deterministic and low-latency. If the render loop takes 20ms for a complex frame, the audio callback starves and produces clicks/pops. Conversely, if audio synthesis is slow, it blocks rendering.
**Do this instead:** Audio runs on its own thread via sounddevice's callback mechanism. The render loop pushes physics parameters to a lock-free queue. The audio callback reads the latest values and synthesizes independently. They share only a few floats through the queue.

### Anti-Pattern 4: Reading Back GPU Buffers Every Frame

**What people do:** Call `buffer.read()` or `framebuffer.read()` every frame to inspect particle state or get pixel data for the HUD.
**Why it's wrong:** GPU readback is synchronous -- it forces a pipeline stall, waiting for all GPU work to complete before transferring data back to CPU. This can add 5-15ms of latency per readback.
**Do this instead:** Only read back when explicitly needed (screenshot capture, video recording frame). For HUD data (particle count, physics readouts), use CPU-side state which is already available from the physics engine. If GPU-side statistics are needed (e.g., how many particles are in a region), use atomic counters read back once per second, not per frame.

### Anti-Pattern 5: Recreating GPU Resources Per Frame

**What people do:** Create new Buffer, Program, or Texture objects inside the render loop.
**Why it's wrong:** GPU resource allocation is expensive (driver calls, memory allocation, compilation). Creating a shader program takes 10-100ms. Creating buffers triggers memory mapping.
**Do this instead:** Create all GPU resources at initialization. Reuse buffers by writing new data (`buffer.write()`). Swap between pre-compiled shader programs. Only recreate resources when the window resizes (framebuffers) or on explicit reload.

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Physics <-> Rendering** | Physics produces scalar uniforms (float values); Rendering consumes them as shader uniforms | One-way flow. Physics has no knowledge of rendering. Clean boundary: a `PhysicsState` dataclass passed each frame. |
| **Physics <-> Audio** | Physics pushes state to thread-safe queue; Audio pops latest | Lossy, non-blocking. Audio thread may skip intermediate states. Use `collections.deque(maxlen=1)` or similar. |
| **Era Manager <-> All Systems** | Era Manager produces `EraConfig` + blend factor; consumed by rendering (shader choice), audio (profile), HUD (text), camera (path) | Central coordination point. Era Manager is the "conductor" that tells everyone what phase we're in. |
| **Camera <-> Rendering** | Camera produces view+projection matrices; Rendering uploads as uniforms | Camera has no knowledge of what is being rendered. It only knows about position, target, and field of view. |
| **Input <-> Camera + State** | Input handler dispatches events: mouse drag -> camera, keyboard -> pause/resume/speed | Thin dispatcher. Input handler does not process events itself; it routes to the appropriate system. |
| **Capture <-> Framebuffer** | Capture system reads from the final framebuffer on demand | Only triggered by user action (key press). Not part of the normal render loop. For video, reads every frame into an ffmpeg pipe. |

### External Dependencies

| Dependency | Role | Integration Notes |
|------------|------|-------------------|
| **ModernGL** | OpenGL context, buffers, shaders, framebuffers | Core dependency. All GPU operations go through this. Requires OpenGL 4.3+ for compute shaders. |
| **moderngl-window** | Window creation, event loop, input handling | Provides the WindowConfig base class and main loop. Handles platform differences (Windows/Linux/Mac). |
| **NumPy** | Initial particle data generation, physics calculations | Used at initialization for generating particle arrays, and each frame for physics uniform computation. |
| **sounddevice** | Audio output stream with callback | Wraps PortAudio. Callback runs on a separate OS thread. Requires careful thread-safety. |
| **Pillow** | Screenshot saving (PNG) | Used only for capture. Converts raw framebuffer bytes to image format. |
| **pyimgui** | HUD overlay rendering | Optional but recommended. Integrates with moderngl-window. Alternative: custom bitmap font renderer. |

## Build Order (Dependency Chain)

The components have clear dependency relationships that dictate build order:

```
Phase 1: Foundation (no dependencies between these)
   [Window + Event Loop] -- can render a blank screen
   [Physics Engine]      -- can compute cosmology values standalone (testable without GPU)

Phase 2: Core Rendering (depends on Phase 1)
   [Particle System]     -- needs Window (OpenGL context) + Physics (uniforms)
   [Camera System]       -- needs Window (for input events + projection)
   [Shader Manager]      -- needs Window (OpenGL context)

Phase 3: Visual Polish (depends on Phase 2)
   [Era Manager]         -- needs Physics + Shader Manager + Particle System
   [Framebuffer Pipeline + Post-Processing] -- needs Shader Manager + a scene to render

Phase 4: Presentation (depends on Phase 2-3)
   [HUD / Overlay]       -- needs Era Manager (for text) + a rendered scene
   [Audio Engine]         -- needs Physics (for parameters); independent of rendering
   [Capture System]      -- needs Framebuffer Pipeline (for readback)
```

**Key insight:** The Physics Engine and the Window/Rendering foundation are independent and can be built in parallel. The Era Manager is the integration nexus -- it does not work until physics, shaders, and particles all exist. Audio is the most independent subsystem and can be built at any phase after physics exists.

## Sources

- [ModernGL 5.12.0 Documentation - ComputeShader](https://moderngl.readthedocs.io/en/latest/reference/compute_shader.html)
- [ModernGL 5.12.0 Documentation - Framebuffer](https://moderngl.readthedocs.io/en/latest/reference/framebuffer.html)
- [ModernGL Rendering Pipeline (DeepWiki)](https://deepwiki.com/moderngl/moderngl/5.1-basic-rendering-pipeline)
- [ModernGL ParticleSim (Compute Shaders + SSBOs)](https://github.com/casparmaria/ModernGL_ParticleSim)
- [moderngl-window Basic Usage](https://moderngl-window.readthedocs.io/en/latest/guide/basic_usage.html)
- [moderngl-window ImGui Integration Example](https://github.com/moderngl/moderngl-window/blob/master/examples/integration_imgui.py)
- [Game Loop Pattern (Game Programming Patterns)](https://gameprogrammingpatterns.com/game-loop.html)
- [LearnOpenGL - Bloom](https://learnopengl.com/Advanced-Lighting/Bloom)
- [LearnOpenGL - Instancing](https://learnopengl.com/Advanced-OpenGL/Instancing)
- [Rendering Particles with Compute Shaders (Mike Turitzin)](https://miketuritzin.com/post/rendering-particles-with-compute-shaders/)
- [NVIDIA: SSBO Double Buffering with Compute Shaders](https://forums.developer.nvidia.com/t/ssbo-double-buffering-with-compute-shaders/50573)
- [python-sounddevice Real-time Audio Processing (DeepWiki)](https://deepwiki.com/spatialaudio/python-sounddevice/4.3-real-time-audio-processing)
- [GLSL Colormap Shaders (kbinani)](https://github.com/kbinani/colormap-shaders)
- [pytransitions/transitions (Python State Machine)](https://github.com/pytransitions/transitions)
- [pyimgui Documentation](https://pyimgui.readthedocs.io/en/latest/guide/first-steps.html)
- [CMU Framebuffers, Offscreen Rendering, and Post-Processing](https://15466.courses.cs.cmu.edu/lesson/framebuffers)

---
*Architecture research for: BigBangSim -- Real-time cosmological simulation visualization*
*Researched: 2026-03-27*
