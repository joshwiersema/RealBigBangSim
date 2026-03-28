# Project Research Summary

**Project:** BigBangSim -- Cinematic Cosmological Big Bang Simulation
**Domain:** Real-time GPU-accelerated scientific visualization (desktop application)
**Researched:** 2026-03-27
**Confidence:** HIGH

## Executive Summary

BigBangSim is a cinematic, educational desktop application that renders the full 13.8-billion-year history of the universe as an interactive, real-time GPU particle simulation with physics-driven generative audio. No existing consumer product occupies this niche: SpaceEngine explores the present universe, Universe Sandbox is a gravity sandbox, Illustris TNG targets researchers, and NASA SVS produces pre-rendered videos. BigBangSim is the interactive documentary of cosmic history. The recommended stack is Python 3.11 with ModernGL (OpenGL 4.3 compute shaders), PyGLM for 3D math, pyo for generative audio (with sounddevice as fallback), and imgui-bundle for educational HUD overlays. This stack is well-supported, actively maintained, and maps cleanly to the project's requirements.

The architecture follows a strict four-layer separation: Application (window, input, state machine), Simulation (physics engine, era manager, timeline controller), Rendering (particle system via compute shaders, shader manager, camera, post-processing), and Presentation (HUD, audio, capture). The critical architectural pattern is data-driven era configuration: each of the 11 cosmological eras is defined as a data record controlling physics, visuals, audio, and camera behavior, with interpolated transitions between them. Particle data lives entirely on the GPU after initialization, updated by compute shaders in a ping-pong double-buffer pattern. The physics engine feeds only a handful of scalar uniforms per frame. This design supports 1M particles at 30+ FPS on a GTX 1060.

The top risks are: (1) logarithmic time-scale design -- the timeline spans 60 orders of magnitude and a naive linear mapping makes most eras invisible; this is the single most important design decision and must be solved in Phase 1; (2) floating-point precision across cosmic scales, mitigated by camera-relative rendering and per-era coordinate systems; (3) the pyo audio library being pinned to Python 3.11 with uncertain future releases, mitigated by an audio abstraction layer with a sounddevice+numpy fallback; and (4) scientific inaccuracy, mitigated by a centralized constants module citing Planck 2018 and PDG values. All four critical pitfalls require Phase 1 architectural decisions that cannot be retrofitted later.

## Key Findings

### Recommended Stack

The stack centers on Python 3.11 (pinned for pyo audio compatibility) with ModernGL 5.12.0 as the shader-first OpenGL 4.3 binding. ModernGL provides compute shader access essential for GPU-side particle updates, and its companion moderngl-window handles cross-platform windowing with built-in imgui integration. Scientific computing uses NumPy 2.2.x for bulk array operations and SciPy 1.14.x for signal processing and special functions (Saha equation, nucleosynthesis calculations). See STACK.md for full version pins and rationale.

**Core technologies:**
- **ModernGL 5.12.0 + GLSL 4.30**: GPU rendering and compute shaders -- the only viable approach for 1M particles at 30+ FPS in Python
- **PyGLM 2.8.3**: 3D math (matrices, vectors, quaternions) -- C++ core, 10-100x faster than numpy for individual transforms, GLM-compatible API matching GLSL conventions
- **pyo 1.0.5 / sounddevice 0.5.5**: Generative audio synthesis -- pyo provides rich DSP primitives (oscillators, filters, granular synthesis); sounddevice is the fallback if pyo is unavailable
- **imgui-bundle 1.92.601**: Educational HUD overlay -- Dear ImGui v1.90.9+ with ImPlot for real-time graphs, native moderngl-window integration
- **NumPy 2.2.x + SciPy 1.14.x**: Scientific computing -- particle initialization, physics parameter computation, audio filter design
- **Pillow 12.1.1 + FFmpeg (subprocess)**: Capture -- screenshots via framebuffer read, video recording via raw frame pipe to FFmpeg

**Critical version constraint:** Python must be 3.11.x. The pyo audio library only ships PyPI wheels for Python 3.7-3.11. All other dependencies support 3.11. If pyo is dropped, Python 3.12+ becomes viable.

### Expected Features

**Must have (table stakes -- P1 for launch):**
- Real-time 3D particle rendering (100K+ instanced billboard particles, compute shader updates)
- Smooth camera controls (orbit, zoom, pan with damping)
- Play/pause/speed controls (spacebar, +/- keys)
- Era labels and timeline indicator (logarithmic time mapping)
- Basic physics readouts HUD (temperature, density, scale factor)
- Visually distinct eras (minimum 3-4: plasma, recombination, dark ages, first stars)
- Post-processing effects (bloom, HDR tone mapping)
- Screenshot capture (F12 to PNG)

**Should have (differentiators -- P2, add once core works):**
- Complete 13.8-billion-year cinematic journey through all 11 eras
- Physics-driven generative ambient soundscape tied to live simulation parameters
- Rich educational overlays with contextual "what's happening and why" explanations
- Cinematic auto-camera with scripted keyframed paths per era
- Milestone markers ("First atoms form", "CMB released", "First stars ignite")
- Per-era particle behavior driven by real cosmological equations (Friedmann, BBN, Saha, Jeans)

**Defer (v2+):**
- Video recording (MP4 export via FFmpeg) -- requires frame-locked rendering and async PBO readback
- Accessibility features (colorblind palettes, high-contrast mode)
- Configurable HUD density, localization, high-res screenshot mode

**Explicit anti-features (do not build):**
- Full N-body gravity simulation (intractable at cosmological scale; use statistical approximations)
- VR/AR support, web deployment, mobile support (scope killers)
- User-defined custom simulations / sandbox mode (testing matrix explodes, accuracy impossible)
- Real-time parameter editing panel (exposes internals that confuse non-experts)

### Architecture Approach

The architecture is a four-layer stack (Application, Simulation, Rendering, Presentation) with strict one-way data flow from physics to GPU. The simulation layer is pure Python with no rendering dependencies, making it independently testable. The rendering layer owns all GPU state (ModernGL contexts, buffers, shaders, framebuffers). The two layers communicate through a `PhysicsState` dataclass containing scalar values (temperature, density, scale factor, Hubble parameter) that become shader uniforms. Audio runs on its own thread, receiving physics parameters via a thread-safe queue. The Era Manager acts as the central "conductor" coordinating all systems. See ARCHITECTURE.md for the full component diagram and data flow.

**Major components:**
1. **Physics Engine** -- Computes cosmological parameters per timestep using Friedmann equations, Saha equation, Jeans instability; produces scalar uniforms for GPU
2. **Particle System** -- GPU-resident SSBOs with ping-pong double buffering; compute shader updates all particles in parallel; data never leaves the GPU during normal operation
3. **Era Manager** -- Data-driven configuration of all 11 eras (time boundaries, physics params, shader variant, color palette, audio profile, camera path, HUD text); interpolates between eras during transitions
4. **Timeline Controller** -- Maps wall-clock time to cosmic time via piecewise logarithmic function; allocates configurable "screen time budgets" per era
5. **Post-Processing Chain** -- Multi-pass framebuffer pipeline: HDR scene render, bloom extraction, Gaussian blur, tone mapping, composite
6. **Audio Engine** -- Runs on separate thread via sounddevice/pyo callback; maps physics parameters to oscillator frequencies, filter cutoffs, amplitudes

### Critical Pitfalls

1. **Logarithmic time-scale collapse** -- The timeline spans 60 orders of magnitude. A linear mapping makes early eras invisible. Design a piecewise time-mapping function with per-era "screen time budgets" as a first-class configuration in Phase 1. This is foundational; every other system depends on it.

2. **Floating-point precision at cosmic scales** -- Float32 has 7 digits of precision. Particle positions spanning sub-atomic to cosmic scales cause visible grid-snapping and jitter. Use camera-relative rendering (transform positions relative to camera before GPU upload) and per-era coordinate systems. Must be designed in Phase 1; cannot be retrofitted.

3. **CPU-bound particle updates** -- Python loops over 1M particles are 50-100ms per frame. Compute shaders from day one are mandatory, not an optimization. The GPU architecture is fundamentally different from CPU iteration and cannot be migrated later.

4. **Era transition discontinuities ("jump cuts")** -- Each era has radically different visuals. Without explicit transition periods (cross-fade shaders, interpolated particle properties), the simulation feels like a slideshow. Design transitions alongside eras, not as polish.

5. **Scientific inaccuracy** -- Wrong constants propagate through every system. Centralize all cosmological parameters in a single module citing Planck 2018 (arXiv:1807.06209) and PDG values. Every number must have a source comment. Continuous concern across all phases.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Foundation -- Window, Physics Engine, Time System

**Rationale:** The architecture research identifies three independent foundations: the OpenGL window/context, the physics engine, and the timeline controller. All downstream systems depend on these. The two most critical pitfalls (logarithmic time-scale collapse and floating-point precision) must be solved here. The physics engine is independently testable without a GPU context.

**Delivers:** An OpenGL 4.3 window (ModernGL + moderngl-window) rendering a blank scene with an orbit camera. A standalone physics engine computing cosmological parameters (scale factor, temperature, density, Hubble parameter) for all 11 eras. A timeline controller with piecewise logarithmic time mapping and configurable per-era screen time budgets. A centralized cosmological constants module with cited Planck 2018 / PDG values.

**Addresses features:** Window + camera system, play/pause/speed controls, logarithmic time mapping
**Avoids pitfalls:** Logarithmic time-scale collapse (P1), floating-point precision (P1), scientific inaccuracy (constants module)

### Phase 2: Core Rendering -- Particle System, Shader Architecture, Post-Processing

**Rationale:** With the foundation in place, the rendering pipeline can be built. Architecture research shows the particle system, shader manager, and framebuffer pipeline are tightly coupled and should be built together. The compute shader vs. CPU decision is architectural and must happen here. The "mega-shader trap" pitfall demands a modular shader architecture from the first shader written.

**Delivers:** GPU-resident particle system with compute shader updates (ping-pong SSBO). Modular shader architecture with shared includes and per-era fragment shaders. HDR framebuffer pipeline with bloom and tone mapping. At least 2-3 visually distinct era looks (plasma, neutral gas, star formation) as proof of the shader architecture. 100K+ particles at 30+ FPS.

**Addresses features:** Real-time 3D particle rendering, post-processing (bloom, tone mapping), visually distinct eras (initial set)
**Avoids pitfalls:** CPU-bound particle updates (compute shaders from day one), mega-shader trap (modular shader architecture)
**Uses stack:** ModernGL 5.12.0, GLSL 4.30, PyGLM 2.8.3, NumPy 2.2.x

### Phase 3: Era Content -- All 11 Eras, Transitions, Physics-Driven Visuals

**Rationale:** The rendering pipeline and physics engine are proven. Now populate all 11 cosmological eras with correct physics models, visual styles, and smooth transitions. The "era transition discontinuities" pitfall and "visualizing the unvisualizable" pitfall are addressed here. This is the most content-heavy phase and the core of the product's value.

**Delivers:** All 11 eras with per-era physics kernels (inflation, nucleosynthesis, recombination, Jeans instability, etc.), distinct visual styles, and smooth cross-fade transitions. Data-driven era configuration files. Early eras (Planck through QGP) use defensible artistic interpretations with educational overlay disclaimers. Full timeline playthrough with zero jump cuts.

**Addresses features:** All 11 cosmological eras, per-era particle behavior, visually distinct eras (complete), era labels + timeline bar
**Avoids pitfalls:** Era transition discontinuities (transitions designed alongside eras), visualizing the unvisualizable (artistic interpretation framework)

### Phase 4: Presentation -- HUD, Audio, Cinematic Camera

**Rationale:** Architecture research shows audio and HUD are the most independent subsystems -- they enhance the experience but do not block core rendering. The cinematic auto-camera requires visually complete eras (Phase 3) to design meaningful paths. Audio requires a working physics engine (Phase 1) to drive parameters. Building these after the visual pipeline is complete allows tuning audio-visual coherence.

**Delivers:** Educational HUD overlay (imgui-bundle) with era descriptions, physics readouts, milestone markers. Generative ambient soundscape (pyo/sounddevice) driven by live temperature, density, expansion rate. Cinematic auto-camera with per-era keyframed paths. Screenshot capture.

**Addresses features:** Physics readouts HUD, educational overlays, generative soundscape, cinematic auto-camera, milestone markers, screenshot capture
**Avoids pitfalls:** Audio-visual disconnect (audio built after visuals are tuned), HUD information overload (progressive disclosure design)
**Uses stack:** imgui-bundle 1.92.601, pyo 1.0.5 / sounddevice 0.5.5, Pillow 12.1.1

### Phase 5: Polish -- Video Recording, Accessibility, Final Tuning

**Rationale:** Video recording requires frame-locked rendering decoupled from wall-clock time, plus async PBO readback to avoid pipeline stalls. This is meaningfully complex and should only be tackled after the cinematic camera path and audio are complete (the recorded video is the flagship shareable output). Accessibility and UX polish follow user testing.

**Delivers:** MP4 video export of full cinematic run with audio. Async PBO readback for stall-free capture. UX polish: scale indicator, adaptive HUD text contrast, progressive disclosure refinement. Accessibility features (colorblind palette, keyboard-only navigation).

**Addresses features:** Video recording, accessibility, configurable HUD density
**Uses stack:** FFmpeg (subprocess), Pillow

### Phase Ordering Rationale

- **Phase 1 before Phase 2:** The physics engine and timeline controller produce the data that drives everything else. The OpenGL context must exist before any GPU work. Both critical "foundational" pitfalls (time mapping, float precision) are addressed here.
- **Phase 2 before Phase 3:** The shader architecture and compute pipeline must be proven before populating 11 eras of content. Building eras on an unproven renderer means rework.
- **Phase 3 before Phase 4:** Audio, HUD, and camera are enhancement layers. The cinematic camera needs visual landmarks to navigate around. Audio needs physics parameters to sonify. Building these before visuals are complete means tuning them twice.
- **Phase 4 before Phase 5:** Video recording captures the complete experience (visuals + audio + camera + HUD). It is the last integration point and should only run after all content is finalized.
- **Physics engine and window are parallel within Phase 1:** Architecture research confirms these are independent. Physics is testable without a GPU.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1 (Timeline Controller):** The piecewise logarithmic time-mapping function is novel and project-specific. No off-the-shelf solution exists. Needs careful design and iterative tuning. Research the conformal time / log-time approach to Friedmann equation integration.
- **Phase 3 (Era Content):** Each of the 11 eras requires domain-specific physics research (nucleosynthesis yields, Saha equation parameterization, Jeans mass calculation, Press-Schechter formalism). Sparse documentation on visualizing pre-recombination eras. Per-era research sprints recommended.
- **Phase 4 (Generative Audio):** Physics-to-audio parameter mapping is creative/experimental. No established best practices for sonifying cosmological data in real time. NASA sonification project is a reference but uses different methodology. Prototype early within the phase.

Phases with standard patterns (skip research-phase):
- **Phase 2 (Core Rendering):** Compute shader particle systems, instanced rendering, bloom post-processing, and ping-pong SSBO patterns are well-documented with ModernGL examples and LearnOpenGL tutorials. Community examples exist for 1M+ particles.
- **Phase 5 (Video Recording):** FFmpeg subprocess piping, PBO readback, and frame-locked recording are well-documented patterns. No novel engineering required.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All core libraries verified on PyPI with recent releases and active maintenance. Version compatibility confirmed. Only medium-confidence item is pyo's release cadence (mitigated by fallback). |
| Features | HIGH | Feature landscape based on analysis of 5+ competitor products (SpaceEngine, Universe Sandbox, Illustris TNG, NASA SVS, PhET). Clear differentiation identified. Anti-features well-justified. |
| Architecture | HIGH | Core rendering pipeline patterns (compute shaders, ping-pong SSBO, multi-pass FBO, fixed-timestep simulation) are industry-standard with multiple verified sources. Cosmological-specific layering is MEDIUM. |
| Pitfalls | HIGH | All 7 critical/major pitfalls sourced from multiple independent references (GPU rendering literature, scientific visualization papers, community forums). Prevention strategies are concrete and actionable. |

**Overall confidence:** HIGH

### Gaps to Address

- **pyo long-term viability:** The pyo audio library has not published to PyPI since March 2023. Version 1.0.6 exists on GitHub but is unreleased. Monitor the situation; if pyo becomes unmaintainable, the sounddevice+numpy+scipy fallback path must become the primary path. This is a Phase 4 decision point.
- **Early-era visual language:** No established conventions exist for visualizing the Planck epoch, Grand Unification, or Electroweak symmetry breaking. The visual approach for these eras is necessarily artistic interpretation. Plan for creative experimentation in Phase 3 with explicit educational disclaimers.
- **Performance at 1M particles on GTX 1060:** Community examples demonstrate 1M+ particles with compute shaders, but this project's per-particle physics may be more complex than typical demos. Profile early in Phase 2 and be prepared to reduce particle count or simplify per-particle compute.
- **Friedmann equation numerical stability:** The ODE solver must handle stiff transitions (radiation-to-matter dominance). Pre-compute the scale factor table at startup using SciPy's implicit solvers (Radau/BDF); do not solve ODEs in the render loop. Validate against published Planck 2018 results.
- **imgui-bundle + moderngl-window integration:** While documented, the integration of imgui-bundle (not pyimgui) with moderngl-window may have edge cases. Verify the integration path works in Phase 1 or early Phase 4 with a minimal prototype.

## Sources

### Primary (HIGH confidence)
- [Planck 2018 Results VI: Cosmological Parameters (arXiv:1807.06209)](https://arxiv.org/abs/1807.06209) -- definitive cosmological constants
- [PDG Review: Big Bang Nucleosynthesis](https://pdg.lbl.gov/2024/reviews/rpp2024-rev-bbang-nucleosynthesis.pdf) -- BBN yields, lithium problem
- [ModernGL 5.12.0 Documentation](https://moderngl.readthedocs.io/en/latest/) -- compute shaders, framebuffers, rendering pipeline
- [moderngl-window Documentation](https://moderngl-window.readthedocs.io/en/latest/) -- windowing, event loop, imgui integration
- [LearnOpenGL Bloom Tutorial](https://learnopengl.com/Advanced-Lighting/Bloom) -- multi-pass post-processing
- [Game Loop Pattern (Game Programming Patterns)](https://gameprogrammingpatterns.com/game-loop.html) -- fixed-timestep simulation

### Secondary (MEDIUM confidence)
- [ModernGL_ParticleSim (GitHub)](https://github.com/casparmaria/ModernGL_ParticleSim) -- compute shader particle system example (2^27 particles at 60 FPS)
- [PyGLM PyPI/GitHub](https://pypi.org/project/PyGLM/) -- 3D math library, actively maintained
- [imgui-bundle PyPI](https://pypi.org/project/imgui-bundle/) -- Dear ImGui 1.90.9+ bindings
- [pyo Documentation](https://belangeo.github.io/pyo/) -- generative audio synthesis
- [sounddevice Real-time Audio (DeepWiki)](https://deepwiki.com/spatialaudio/python-sounddevice/4.3-real-time-audio-processing) -- audio callback patterns
- [NASA Chandra Sonification](https://chandra.si.edu/sound/) -- data-to-sound methodology reference
- [PhET Research](https://phet.colorado.edu/en/research) -- educational simulation design principles

### Tertiary (LOW confidence)
- [Outerra Logarithmic Z-Buffer](https://outerra.blogspot.com/2009/08/logarithmic-z-buffer.html) -- reversed-Z technique (older post, principles still valid)
- [Cinematic Scientific Visualization (LSE)](https://blogs.lse.ac.uk/impactofsocialsciences/2022/03/16/introducing-cinematic-scientific-visualization-a-new-frontier-in-science-communication/) -- accuracy vs. intelligibility tradeoffs
- [Numerical Solving of Friedmann Equations (dournac.org)](https://dournac.org/info/friedmann) -- stiff ODE reference

---
*Research completed: 2026-03-27*
*Ready for roadmap: yes*
