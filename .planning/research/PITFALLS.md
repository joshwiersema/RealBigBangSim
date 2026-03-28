# Pitfalls Research

**Domain:** Cosmological Big Bang simulation visualization (Python/ModernGL/GLSL desktop app)
**Researched:** 2026-03-27
**Confidence:** HIGH (multiple verified sources across GPU rendering, scientific simulation, and cosmology domains)

## Critical Pitfalls

### Pitfall 1: Logarithmic Time Scale Collapse

**What goes wrong:**
The cosmic timeline spans from 10^-43 seconds (Planck epoch) to ~4x10^17 seconds (13.8 billion years). A naive linear time mapping means the first microsecond of the universe -- where most of the interesting early physics happens (inflation, quark-gluon plasma, hadron epoch, nucleosynthesis) -- occupies zero perceptible screen time, while the Dark Ages (lasting hundreds of millions of years with almost nothing visually happening) dominates the simulation. The user sees nothing for the first 90% of the runtime, then a brief flash of galaxy formation.

**Why it happens:**
Developers think in wall-clock time or linear cosmic time. The 11 cosmological eras listed in PROJECT.md span roughly 60 orders of magnitude in time. No linear mapping can make all of them watchable. This is the single most important design decision in the entire project.

**How to avoid:**
- Design a piecewise time-mapping function that allocates deliberate "screen time budgets" to each era, independent of actual cosmic duration. Each era gets a configurable number of seconds of real-time display.
- Within each era, use logarithmic time progression where physical processes span many orders of magnitude (e.g., nucleosynthesis: 10 seconds to ~20 minutes of cosmic time compressed to ~30 seconds of screen time).
- Expose the time-mapping as a first-class configuration, not buried in the simulation loop. This will be tuned endlessly.
- The Friedmann equation integration for scale factor a(t) should use conformal time or log-time internally to maintain numerical stability across these scales.

**Warning signs:**
- Early eras flash by in under a second during testing
- You find yourself adding `time.sleep()` hacks to slow down early eras
- The simulation "feels empty" for long stretches (Dark Ages)
- Physics parameters (temperature, density) jump discontinuously between eras

**Phase to address:**
Phase 1 (Core architecture). The time-mapping system is foundational -- every other system (physics, visuals, audio, camera, HUD) depends on it. Getting this wrong means rewriting everything.

---

### Pitfall 2: Floating-Point Precision Catastrophe at Cosmic Scales

**What goes wrong:**
32-bit floats (which GLSL uses by default) have ~7 decimal digits of precision. When the simulation transitions from sub-atomic scales (early universe, ~10^-15 meters) to cosmic scales (large-scale structure, ~10^26 meters), particle positions become quantized to increasingly coarse grids. Visible symptoms: particles "snap" to invisible grid positions, jitter in place, cluster into sheets/planes instead of smooth distributions. At the edge of a galaxy-scale simulation with single-precision coordinates, position accuracy degrades to ~130 km -- particles jump in 130 km increments.

**Why it happens:**
It is natural to use a single coordinate system spanning the entire simulation. OpenGL vertex positions are 32-bit floats by default. The ratio between smallest meaningful distance and largest distance in a cosmological simulation exceeds 10^40, while float32 can only represent a ratio of ~10^7 with sub-unit precision.

**How to avoid:**
- **Camera-relative rendering**: Transform all particle positions relative to the camera before sending to the GPU. This keeps vertex coordinates near zero where float32 precision is best. This is the standard technique used in space games and cosmological visualizations.
- **Era-specific coordinate systems**: Each cosmological era operates at a fundamentally different scale. Reset the coordinate origin and scale factor at each era transition rather than maintaining one coordinate space.
- **Scale factor normalization**: Store particle positions as dimensionless fractions of the current "viewport scale" (e.g., 0.0 to 1.0), and let uniforms carry the physical scale metadata for the HUD. The GPU never sees raw physical coordinates.
- **Reversed depth buffer**: Use a reversed-Z depth buffer (near=1.0, far=0.0) to distribute depth precision more evenly, avoiding z-fighting between overlapping transparent layers (critical for nebula/gas cloud rendering).

**Warning signs:**
- Particles visibly snap to grid positions when zoomed in
- Jittering/flickering of particles that should be stationary
- Z-fighting between overlapping transparent surfaces (gas clouds, nebulae)
- Galaxy arms or filaments appear as staircase patterns instead of smooth curves

**Phase to address:**
Phase 1 (Core architecture). The coordinate system and rendering pipeline design is foundational. Retrofitting camera-relative rendering onto an existing system is a major rewrite.

---

### Pitfall 3: The "One Mega-Shader" Trap

**What goes wrong:**
Developers try to write a single GLSL shader program that handles all 11 cosmological eras using uniform-driven branching (`if (era == PLANCK) ... else if (era == INFLATION) ...`). This shader grows to hundreds or thousands of lines, becomes impossible to debug, and on some GPU architectures the branching causes severe performance degradation because all branches execute and results are masked (SIMD execution model). Fragment shaders with per-pixel branching on computed values are the worst offenders.

**Why it happens:**
Switching shader programs has overhead, and the "just add another branch" approach feels simpler than managing multiple shader variants. Early eras may look similar enough that branching seems reasonable. But each era has fundamentally different visual requirements: pure energy fields (Planck), expanding space distortion (inflation), hot plasma glow (QGP), discrete particle formation (hadron), nuclear reaction visualization (nucleosynthesis), surface of last scattering (CMB), darkness with faint density fluctuations (Dark Ages), point light sources igniting (first stars), rotating disk formation (galaxies).

**How to avoid:**
- Design a shader library architecture from the start: shared utility functions (noise, color mapping, easing) in include files, with per-era vertex and fragment shaders that compose these utilities.
- Use ModernGL's `Program` objects to compile separate shader programs per era (or per visual style). Switching between 5-10 programs per frame is negligible overhead compared to the rendering itself.
- Use uniform buffer objects (UBOs) for shared state (time, camera, global physics parameters) so shader switching does not require re-uploading common data.
- Keep branching only for within-era variations (e.g., different particle types within the quark-gluon plasma era), not for cross-era logic.

**Warning signs:**
- Your vertex or fragment shader exceeds ~150 lines
- You have `if/else` chains in fragment shaders testing a "current era" uniform
- Performance drops when adding a new era's visual logic
- Shader compilation takes noticeably long (sign of excessive code paths)
- Visual artifacts appear in era A when you modify era B's shader code

**Phase to address:**
Phase 2 (Rendering pipeline). Must be established when the first shader is written. The shader architecture pattern must be decided before any era-specific visuals are implemented.

---

### Pitfall 4: CPU-Bound Particle Updates Destroying Frame Rate

**What goes wrong:**
Python updates 100K-1M particle positions on the CPU per frame, then uploads the entire position buffer to the GPU. At 100K particles x 12 bytes (vec3) = 1.2 MB per frame at 60 FPS = 72 MB/s of CPU-to-GPU transfer. At 1M particles = 720 MB/s, which saturates PCIe bandwidth and the Python loop updating positions takes 50-100ms per frame (well over the 16ms budget for 60 FPS, or even the 33ms budget for 30 FPS). Result: slideshow.

**Why it happens:**
Python developers instinctively write `for particle in particles: particle.update()` loops. This is catastrophically slow due to Python interpreter overhead (even with NumPy vectorization, the CPU-GPU transfer remains). The temptation is to "get it working first" on CPU, planning to "optimize later" -- but the architecture for GPU-side computation is fundamentally different from CPU-side iteration.

**How to avoid:**
- **Compute shaders from the start** (requires OpenGL 4.3, which ModernGL supports): Particle positions and velocities live in GPU storage buffers (SSBOs). A compute shader updates all particles in parallel on the GPU. The data never leaves the GPU. This is the only viable approach for 1M particles at 30+ FPS.
- **Transform feedback as fallback**: If targeting OpenGL 3.3 hardware, use transform feedback to ping-pong between two vertex buffers, updating positions in the vertex shader. Less flexible than compute but still GPU-side.
- **Never allocate per-frame**: Pre-allocate all GPU buffers at startup. Use `buffer.write()` only for uniform updates, not particle data.
- **Profile early**: Use ModernGL's query objects or `glFinish()` timing to measure actual GPU frame time from the first prototype.

**Warning signs:**
- FPS drops below 30 with only 10K particles
- `cProfile` shows most time in the particle update loop, not in `ctx.render()`
- Adding more particles causes linear FPS degradation
- GPU utilization (check with Task Manager or `nvidia-smi`) is low while CPU is pegged

**Phase to address:**
Phase 1-2 (Core architecture / Rendering pipeline). The decision to use compute shaders vs. transform feedback vs. CPU updates is architectural. It cannot be changed later without rewriting the particle system from scratch.

---

### Pitfall 5: Scientific Inaccuracy in "Accurate" Simulation

**What goes wrong:**
The project claims scientific accuracy but uses made-up numbers, incorrect physics models, or outdated parameters. Common errors: wrong Big Bang nucleosynthesis yields (helium mass fraction should be ~0.247, not 0.25), incorrect Hubble constant (Planck 2018: 67.4 km/s/Mpc, not the commonly seen "70"), using Newtonian gravity where general relativity matters, displaying temperature in wrong units or wrong epoch, conflating recombination temperature with CMB temperature today (3000K vs 2.725K), getting the lithium-7 abundance right when the "cosmological lithium problem" means observation and theory disagree by 3x.

**Why it happens:**
Developers copy values from Wikipedia pop-science sections, use rounded numbers for convenience, or implement simplified physics that happens to give wrong results. The Friedmann equations are straightforward but parameterization matters: using radiation density, matter density, and dark energy density from Planck 2018 results requires careful attention to the actual published values and their units.

**How to avoid:**
- Create a single `cosmological_parameters.py` constants module that cites Planck 2018 (arXiv:1807.06209) and PDG values for every constant used. Every number must have a comment with its source and units.
- For BBN yields, use the accepted SBBN predictions: Yp (He-4 mass fraction) = 0.2470 +/- 0.0002, D/H = (2.527 +/- 0.030) x 10^-5, from the PDG review.
- Acknowledge the lithium problem in the educational overlay rather than displaying either the theoretical or observed value as "the answer."
- Use the Saha equation for recombination (not a sudden transition), Friedmann equations for expansion (not linear approximation), and Jeans instability for structure formation.
- Have a "physics review" checklist for each era before marking it complete.

**Warning signs:**
- Constants are hardcoded as magic numbers in shader code or Python files
- Temperature or density displays show values that "look right" but have no cited source
- Educational text contradicts the simulation's actual computed values
- An astrophysicist reviewing the project finds errors in the first 5 minutes

**Phase to address:**
Phase 1 (Core architecture -- constants module) and every subsequent phase (each era's physics must be verified independently). This is a continuous concern, not a one-time fix.

---

### Pitfall 6: Era Transition Discontinuities (The "Jump Cut" Problem)

**What goes wrong:**
Each cosmological era has radically different visual characteristics, particle counts, color palettes, scales, and physics. Naive transitions create jarring "jump cuts" where the screen flashes from one look to a completely different one -- a bright hot plasma suddenly becomes a dark void (CMB to Dark Ages), or scattered particles suddenly form galaxies. The simulation feels like a slideshow of unrelated scenes rather than a continuous cosmic evolution.

**Why it happens:**
Each era is developed independently as its own visual "scene." Developers focus on making each era look good in isolation without planning how to smoothly morph between them. The physics genuinely does change dramatically (e.g., recombination takes the universe from opaque plasma to transparent gas), but abrupt visual changes break the cinematic experience.

**How to avoid:**
- Design explicit transition periods (5-10% of each era's screen time budget) with interpolated visuals: cross-fade shaders, gradually morphing particle properties (color, size, opacity), smoothly scaling coordinate systems.
- Use a "transition manager" that knows about the outgoing and incoming era and blends their visual parameters. Both eras' shaders may need to run simultaneously during transitions.
- For the CMB-to-Dark-Ages transition specifically: fade the surface of last scattering into a dim glow, then slowly darken while introducing faint density perturbation seeds. Do not just cut to black.
- For inflation: the visual of space expanding must be continuous with what came before, not a separate "inflation scene."
- Test the full timeline end-to-end early and frequently, not just individual eras.

**Warning signs:**
- Each era works beautifully in isolation but the full timeline playthrough feels choppy
- Temperature/density readouts jump discontinuously at era boundaries
- The camera position resets or jumps at transitions
- Users describe the experience as "a series of demos" rather than "a journey"

**Phase to address:**
Phase 3 (Era content). Transition design should be specified alongside era design, not added as polish later. Every era implementation must include entry and exit transitions.

---

### Pitfall 7: Visualizing the Unvisualizable (Planck Epoch / Pre-Recombination)

**What goes wrong:**
The earliest eras (Planck epoch, Grand Unification, Electroweak) describe physics where there is no "stuff" to render in any traditional sense -- no particles, no light, no space as we understand it. Developers either (a) leave these eras as a boring placeholder (text on black screen), which kills the cinematic experience, or (b) invent visuals that are scientifically meaningless but look cool, which undermines the "scientifically accurate" claim.

**Why it happens:**
These eras describe physics beyond direct visualization. The Planck epoch involves quantum gravity -- a theory we do not have. The quark-gluon plasma era involves quarks and gluons that are never directly observed. There is no "correct" visual representation because no one has ever seen these phenomena.

**How to avoid:**
- Explicitly categorize eras into "physically representable" (nucleosynthesis onward) and "artistically interpreted" (Planck through QGP). The educational overlay should clearly state when visuals are artistic interpretation vs. computed physics.
- Use abstract mathematical visualizations for early eras: energy field noise patterns driven by temperature/density equations, symmetry-breaking visualized as phase transitions in color/pattern, inflation as exponential scaling of a noise field. These are defensibly "inspired by the physics" without claiming to be literal.
- Draw from established scientific visualization conventions: QGP is commonly rendered as a hot fluid (MIT/CERN visualizations use flowing orange-red fluid metaphors). Adopt community conventions rather than inventing from scratch.
- The educational overlay carries more weight in these eras -- narrate what is happening physically while the visuals provide atmosphere.

**Warning signs:**
- Early eras look identical to a screensaver with no connection to physics
- The educational text says one thing while the visuals show something unrelated
- You cannot explain to a non-physicist what the visuals represent
- The visual complexity of early eras is lower than later eras (should be at least as visually rich)

**Phase to address:**
Phase 2-3 (Rendering pipeline / Era content). The visual language for abstract eras should be designed in the rendering pipeline phase, with specific implementations in the era content phase.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| CPU-side particle updates | Simpler initial code, easier debugging | Complete rewrite needed for >10K particles; fundamentally different architecture | Never for this project -- compute shaders should be the starting point |
| Single coordinate system for all eras | No era transition coordinate logic | Floating point artifacts at extreme scales, z-fighting, jittering | Never -- design era-relative coordinates from the start |
| Hardcoded cosmological constants | Faster initial development | Wrong values propagate, no single source of truth, painful to correct | Only in throwaway prototypes that will be deleted |
| `time.sleep()` for era pacing | Quick way to make early eras visible | Non-deterministic timing, breaks video recording, cannot be sped up/slowed down | Never -- use a proper time-mapping system |
| Pre-recorded audio files per era | Avoids generative audio complexity | No connection between sound and physics state, no smooth transitions, large file sizes | Acceptable as Phase 1 placeholder if generative audio is Phase 3+ |
| `glReadPixels` for video capture | Simple to implement | Blocks the render pipeline, cuts FPS in half, synchronous stall | Only for screenshot capture; video recording needs async PBO readback |
| Monolithic simulation loop | Everything in one file, easy to follow | Cannot test eras independently, cannot run headless physics, everything coupled | Only in first week of prototyping |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| ModernGL + windowing library | Creating context with wrong OpenGL version (3.3 vs 4.3). Compute shaders silently fail if context is 3.3. | Explicitly request OpenGL 4.3 context. Check `ctx.version_code` at startup. Log a clear error if compute shaders are needed but unavailable. |
| ModernGL + NumPy | Passing NumPy arrays with wrong dtype (float64 instead of float32) or wrong memory layout (C-contiguous vs Fortran). Buffer writes silently corrupt data. | Always use `.astype(np.float32)` and verify `.flags['C_CONTIGUOUS']`. Create a helper that validates buffer data before upload. |
| Python audio (PyOpenAL/sounddevice) + render loop | Audio callback runs in a separate thread but shares state with the render loop. Race conditions on physics parameters (temperature, density) cause audio glitches or crashes. | Use a thread-safe queue or atomic values for passing physics state to audio. The audio thread should only read from a snapshot, never from live simulation state. |
| FFmpeg subprocess for video recording | Piping raw frame data to FFmpeg stdin but mismatching pixel format, resolution, or frame rate. Result: corrupted video, wrong colors, wrong speed. | Specify format explicitly: `-f rawvideo -pix_fmt rgb24 -s WxH -r FPS`. Use async PBO readback to avoid stalling the render pipeline. |
| Friedmann equation ODE solver | Using a non-stiff solver (basic Runge-Kutta) for equations that become stiff during radiation-matter transition. Solver either fails or requires impractically small timesteps. | Use `scipy.integrate.solve_ivp` with `method='Radau'` or `'BDF'` (implicit solvers for stiff systems). Pre-compute the scale factor table at startup, do not solve ODEs in the render loop. |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Per-particle Python loop | FPS proportional to 1/N_particles; CPU at 100%, GPU idle | Use compute shaders or NumPy vectorized ops for any CPU-side work; particle physics must run on GPU | Breaks at ~5K particles (~3ms per 1K particles in pure Python) |
| Uploading full particle buffer every frame | Constant high CPU-GPU transfer; FPS drops with particle count | Keep particle data on GPU via SSBOs; only upload changed uniforms per frame | Breaks at ~50K particles (600KB/frame at 60 FPS) |
| Too many draw calls per frame | GPU underutilized, draw call overhead dominates | Batch all particles of the same type into one draw call; use instancing or compute-based rendering | Breaks at ~100 separate draw calls per frame |
| Synchronous framebuffer readback for video recording | FPS halves during recording; visible stutter | Use Pixel Buffer Objects (PBOs) for async readback; double-buffer PBOs for pipelined capture | Breaks immediately at any resolution -- `glReadPixels` is a full pipeline stall |
| Overdraw from transparent particle blending | FPS drops in dense regions (QGP, nebulae); GPU fill-rate limited | Use additive blending (no sort needed), or depth-peel only for scenes requiring order-dependent transparency; limit particle opacity | Breaks at ~10K overlapping transparent particles per pixel |
| Text rendering per frame | HUD text is re-rasterized every frame using Python font library | Pre-render text to textures; only re-render when text content changes; use bitmap font atlas for numeric displays that change frequently | Breaks at moderate HUD complexity (~20 text elements updating per frame) |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Information overload in HUD | User reads text instead of watching the simulation; feels like a textbook, not a cinematic experience | Progressive disclosure: show era name and one key fact by default. Detailed physics (temperature, density, equations) available on hover/keypress. Fade HUD opacity during dramatic visual moments. |
| No sense of scale | User cannot comprehend that the simulation went from 10^-35 meters to 10^26 meters; all eras look similarly sized | Display a persistent "scale indicator" (like a ruler that updates with labels: "1 femtometer", "1 meter", "1 light-year", "1 megaparsec"). Animate scale changes dramatically during transitions. |
| Cinematic camera with no escape | User wants to look at something specific but the auto-camera moves away; feels like watching a video, not exploring | Allow camera pause with spacebar. When paused, switch to orbit/zoom/pan controls. Resume cinematic path from current position, not from where it "should" be. |
| Audio that does not match visuals | Generative soundscape feels arbitrary; user cannot connect sounds to what they see | Explicitly tie audio parameters to displayed physics: higher temperature = higher pitch/intensity, expansion = stretching/reverb, particle formation = percussive pings. Sonification should be intuitive, not requiring explanation. |
| Unreadable text on bright backgrounds | White HUD text disappears against bright plasma eras; dark text invisible during Dark Ages | Use text with contrasting outline/shadow, or render text on semi-transparent dark backgrounds. Adapt text style per era's dominant brightness. |
| No orientation during long eras | User loses track of where they are in the cosmic timeline; "are we done yet?" feeling during Dark Ages | Persistent timeline bar showing all eras with current position highlighted. Show time elapsed and upcoming milestone. Give the user a sense of progress. |

## "Looks Done But Isn't" Checklist

- [ ] **Particle system**: Often missing GPU-side update (particles render but positions are computed on CPU) -- verify with `nvidia-smi` or GPU profiler that GPU utilization is high during particle-heavy scenes
- [ ] **Era transitions**: Often missing interpolation between eras (individual eras work, transitions jump) -- verify by watching full timeline at 2x speed; every transition should be smooth
- [ ] **Scientific constants**: Often missing source citations (numbers are in the code but no one verified them) -- verify every constant traces to Planck 2018 or PDG with a comment
- [ ] **Camera system**: Often missing gimbal lock prevention (camera works until it looks straight up/down, then flips) -- verify by testing orbit camera at all angles including poles
- [ ] **Audio system**: Often missing smooth parameter transitions (audio works per-era but pops/clicks at boundaries) -- verify audio with eyes closed through full timeline; no discontinuities
- [ ] **Video recording**: Often missing frame-accurate timing (recorded video plays at wrong speed or drops frames) -- verify by recording a timed sequence and checking frame count matches expected FPS x duration
- [ ] **HUD readouts**: Often missing unit labels or showing wrong units (temperature in Kelvin displayed without "K", or mixing eV and Kelvin) -- verify every displayed number has correct units and matches the physics model's output
- [ ] **Time display**: Often missing proper scientific notation (displays "10000000000 years" instead of "10 Gyr" or "1x10^10 yr") -- verify all large/small numbers use appropriate notation
- [ ] **Depth buffer**: Often missing reversed-Z setup (works for simple scenes, z-fights with overlapping transparencies) -- verify by zooming into dense gas cloud regions and checking for flickering

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong time-mapping (linear instead of logarithmic) | HIGH | Rewrite the simulation clock, update every system that reads time, re-tune all era durations, re-test all transitions. 1-2 week setback. |
| Float precision artifacts | MEDIUM-HIGH | Implement camera-relative rendering (requires modifying vertex shaders and CPU-side transform pipeline). If coordinate system is deeply embedded, may need to redesign particle data structures. |
| Mega-shader monolith | MEDIUM | Extract per-era shaders from the monolith. Tedious but mechanical. Main risk is introducing bugs during extraction. |
| CPU-bound particles | HIGH | Complete rewrite of particle system from CPU loops to compute shaders. Different data structures, different update logic, different buffer management. Architecture change, not optimization. |
| Wrong scientific constants | LOW | Update the constants module, re-run. Low cost if constants are centralized. HIGH cost if hardcoded throughout shaders and Python files (find-and-replace nightmare). |
| Jarring era transitions | MEDIUM | Add transition shaders and blending logic. Requires both outgoing and incoming era shaders to be available simultaneously. May require refactoring render loop to support multi-shader passes. |
| Audio buffer underruns | LOW-MEDIUM | Increase buffer size (adds latency but fixes glitches). Switch to callback mode if using blocking mode. Use rtmixer if sounddevice callbacks are too slow. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Logarithmic time scale collapse | Phase 1: Core architecture | Play through all 11 eras; each gets at least 10 seconds of screen time; verify with a stopwatch |
| Floating-point precision | Phase 1: Core architecture | Zoom into particles at each era's characteristic scale; no jittering or grid-snapping visible |
| Mega-shader trap | Phase 2: Rendering pipeline | Each era has its own shader program; no `if (era == X)` in fragment shaders; shader file count >= number of visual styles |
| CPU-bound particles | Phase 1-2: Core arch / Rendering | 100K particles at 30+ FPS on GTX 1060; GPU utilization > 50%; CPU particle update time < 1ms |
| Scientific inaccuracy | Phase 1 (constants), all phases (eras) | Every constant in `cosmological_parameters.py` has a citation comment; values match Planck 2018 / PDG to published precision |
| Era transition discontinuities | Phase 3: Era content | Full timeline playthrough has zero "jump cuts"; temperature/density readouts change continuously; camera path is smooth |
| Unvisualizable eras | Phase 2-3: Rendering / Era content | Each early era has a distinct visual style; educational overlay explains what the visuals represent; visuals are consistent with physics described |
| HUD information overload | Phase 4: Polish / UX | User test: show to 3 non-physicists; they can follow the story without reading walls of text |
| Audio-visual disconnect | Phase 4: Polish / UX | Mute audio, watch simulation; unmute -- audio should feel connected to visual changes, not arbitrary |

## Sources

- [Planck 2018 Results VI: Cosmological Parameters](https://arxiv.org/abs/1807.06209) -- definitive source for all cosmological constants
- [PDG Review: Big Bang Nucleosynthesis](https://pdg.lbl.gov/2024/reviews/rpp2024-rev-bbang-nucleosynthesis.pdf) -- BBN yields and the lithium problem
- [Floating Point Precision for 3D Universe (GameDev.net)](https://gamedev.net/forums/topic/466331-floating-point-precision-problem-for-3d-universe/) -- camera-relative rendering and hierarchical coordinates
- [Outerra: Logarithmic Depth Buffer](https://outerra.blogspot.com/2009/08/logarithmic-z-buffer.html) -- reversed-Z and logarithmic depth techniques
- [Depth Buffer Precision (Khronos OpenGL Wiki)](https://www.khronos.org/opengl/wiki/Depth_Buffer_Precision) -- z-fighting prevention
- [OpenGL Particle Systems (Vercidium)](https://vercidium.com/blog/opengl-particle-systems/) -- GPU-side particle techniques
- [Compute Shader vs Transform Feedback (GameDev.net)](https://www.gamedev.net/forums/topic/671627-compute-shader-vs-transform-feedback/) -- 10x perf gain with compute shaders
- [Rendering Particles with Compute Shaders (Mike Turitzin)](https://miketuritzin.com/post/rendering-particles-with-compute-shaders/) -- compute shader particle rendering
- [ModernGL Compute Shader Docs](https://github.com/moderngl/moderngl/blob/main/docs/reference/compute_shader.rst) -- ModernGL compute shader API
- [ModernGL Instanced Rendering Issue #168](https://github.com/moderngl/moderngl/issues/168) -- performance discussion for 1M particles
- [GLSL Branching Performance (shader-tutorial.dev)](https://shader-tutorial.dev/advanced/branching/) -- when branching hurts GPU performance
- [Apple Best Practices for Shaders](https://developer.apple.com/library/archive/documentation/3DDrawing/Conceptual/OpenGLES_ProgrammingGuide/BestPracticesforShaders/BestPracticesforShaders.html) -- shader optimization
- [State Machines in Game Programming Patterns](https://gameprogrammingpatterns.com/state.html) -- state complexity grows O(N^2)
- [Numerical Solving of Friedmann Equations](https://dournac.org/info/friedmann) -- stiff ODE challenges
- [Real-time Video Capture with FFmpeg](https://blog.mmacklin.com/2013/06/11/real-time-video-capture-with-ffmpeg/) -- async framebuffer capture
- [python-sounddevice Real-time Audio](https://deepwiki.com/spatialaudio/python-sounddevice/4.3-real-time-audio-processing) -- audio buffer management
- [python-rtmixer](https://github.com/spatialaudio/python-rtmixer) -- GIL-safe low-latency audio
- [Cinematic Scientific Visualization (LSE Impact Blog)](https://blogs.lse.ac.uk/impactofsocialsciences/2022/03/16/introducing-cinematic-scientific-visualization-a-new-frontier-in-science-communication/) -- accuracy vs intelligibility tradeoffs
- [Examining Data Visualization Pitfalls (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8556474/) -- misleading scientific visualizations
- [Seven HUD Mistakes (thewingless.com)](https://thewingless.com/index.php/2021/05/12/7-obvious-beginner-mistakes-in-your-video-games-hud-from-a-ui-ux-art-director/) -- HUD design anti-patterns
- [Reducing Cognitive Overload (Smashing Magazine)](https://www.smashingmagazine.com/2016/09/reducing-cognitive-overload-for-a-better-user-experience/) -- progressive disclosure patterns

---
*Pitfalls research for: Cosmological Big Bang simulation visualization (BigBangSim)*
*Researched: 2026-03-27*
