# Feature Research

**Domain:** Cosmological Big Bang simulation visualization (cinematic educational desktop application)
**Researched:** 2026-03-27
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist in any real-time cosmological simulation/visualization. Missing these means the product feels broken or incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Real-time 3D particle rendering | Core of any particle simulation; SpaceEngine, Universe Sandbox, and every GPU demo does this | HIGH | 100K-1M instanced billboard particles via GLSL. ModernGL supports instanced rendering. Compute shaders (OpenGL 4.3) preferred for update, but instanced draw with vertex shader fallback covers GTX 1060 target. |
| Smooth camera controls (orbit, zoom, pan) | Every 3D visualization has mouse-driven camera; SpaceEngine sets the bar with cinematic flythroughs | MEDIUM | Orbit camera with smooth damping. Mouse drag = orbit, scroll = zoom, middle-drag = pan. Must feel fluid, not jerky. |
| Play/pause/speed controls | Standard in any simulation from Universe Sandbox to PhET sims; users expect to control time flow | LOW | Play, pause, speed multiplier (0.5x, 1x, 2x, 5x, 10x). Keyboard shortcuts (spacebar = pause, +/- = speed). |
| Era labels and timeline indicator | Any educational timeline tool shows "where you are"; users need orientation across 13.8 billion years | MEDIUM | Visual timeline bar showing current position. Era name prominently displayed. Logarithmic time mapping critical -- Planck epoch is 10^-43 seconds, galaxy formation spans billions of years. |
| Basic physics readouts (temperature, density, scale factor) | Scientific visualizations display key parameters; Illustris TNG shows temperature, density, metallicity overlays | MEDIUM | HUD elements showing current cosmic temperature, matter density, radiation density, scale factor a(t). Values from Friedmann equations and Planck 2018 data. |
| Visually distinct eras | The whole point of a timeline simulation; each era must look different (pure energy vs plasma vs neutral gas vs stars) | HIGH | Requires per-era shader programs or parametric shader with era-driven uniforms. Quark-gluon plasma looks nothing like reionization. Smooth crossfade transitions between eras. |
| Post-processing effects (bloom, tone mapping) | Standard in any modern 3D renderer; SpaceEngine uses extensive post-processing for cinematic feel | MEDIUM | HDR rendering with bloom for hot/bright regions, tone mapping for dynamic range. Essential for making early universe glow feel realistic. |
| Fullscreen mode | Basic expectation for any visual experience application | LOW | Toggle fullscreen/windowed. Remember window position and size. |
| Screenshot capture | SpaceEngine, Universe Sandbox, and every visualization tool offer this | LOW | Capture current frame at render resolution (or higher) to PNG. Single keypress (F12 or similar). |
| Keyboard shortcuts | Power users expect keyboard control; PhET sims rely on keyboard for accessibility | LOW | Documented shortcuts for play/pause, speed, camera reset, screenshot, fullscreen. |

### Differentiators (Competitive Advantage)

Features that set this product apart from existing tools. These are where BigBangSim competes and creates unique value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Complete 13.8 billion year cinematic journey | No existing consumer software does the full Big Bang timeline as a guided cinematic experience. SpaceEngine explores the present universe. Universe Sandbox simulates gravity sandboxes. Illustris TNG is research-grade, not consumer-accessible. This fills a genuine gap. | HIGH | Cinematic auto-camera with scripted path through all 11 cosmological eras. Logarithmic time compression so early-universe microsecond events and billion-year structure formation both get screen time. |
| Physics-driven generative ambient soundscape | NASA's sonification project proves data-to-sound resonates emotionally with audiences. No existing consumer sim ties generative audio to live physics parameters (temperature, density, expansion rate). Pre-recorded soundtracks cannot adapt to simulation state. | HIGH | Map cosmic temperature to pitch/timbre, density to amplitude/texture, expansion rate to rhythm/spacing. PyOpenAL or miniaudio for synthesis. Each era gets a distinct sonic character that evolves continuously. |
| Rich educational overlays with contextual explanations | PhET research shows minimal-text, visual-first educational design drives engagement. Most cosmology sims are either research tools (no explanation) or videos (no interactivity). Combining real-time simulation with contextual "what's happening and why" is the differentiator. | MEDIUM | Era descriptions, milestone markers ("First protons form", "CMB released", "First stars ignite"), physics explanations that appear at key moments. Follow PhET principle: minimal text, maximum visual context. |
| Logarithmic time mapping with intuitive navigation | The cosmic timeline spans 60+ orders of magnitude in time. Linear time compression makes early eras invisible. A well-designed logarithmic time bar -- where the user can see and scrub across all eras -- is genuinely novel for a consumer application. | MEDIUM | Custom timeline widget with logarithmic scale. Click-to-jump to any era. Visual markers for major transitions. Time readout showing both "simulation time" (seconds/years since Big Bang) and "cosmic age" in human-readable units. |
| Video recording of full cinematic run | SpaceEngine has video capture, but capturing a complete guided cosmic journey as a shareable MP4 is a unique output. Think "I ran the Big Bang and here's the movie." | MEDIUM | Record to MP4 via ffmpeg subprocess or hardware-accelerated encoding. Frame-locked recording (decouple render from wall clock) for consistent quality regardless of GPU speed. |
| Per-era particle behavior driven by real physics models | Most particle sims use generic attraction/repulsion. Driving particle behavior from actual cosmological equations (Friedmann expansion, BBN yields, Saha recombination, Jeans instability) makes this genuinely educational, not just pretty. | HIGH | Each era has its own physics kernel: inflation drives exponential expansion, nucleosynthesis creates helium ratio, recombination neutralizes particles, gravity collapses overdensities. Parameters from Planck 2018 and PDG. |
| Milestone markers with "cosmic firsts" | Marking moments like "first atoms", "universe becomes transparent", "first star ignites" provides narrative anchors. This is storytelling through simulation -- no existing real-time sim does this. | LOW | Predefined list of ~20 milestone events with timestamps, triggered as simulation crosses each threshold. Brief overlay text + visual/audio cue. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but would hurt the project if built.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full N-body gravity simulation | "Real physics" sounds impressive; Universe Sandbox does it for small systems | Computationally intractable at cosmological scale. Even Illustris TNG runs on supercomputers. A GTX 1060 cannot do gravitational N-body for 1M particles at 30 FPS. Would dominate development time for marginal visual difference at this scale. | Use approximate methods: Jeans instability for collapse, Press-Schechter for halo statistics, visual clustering driven by density fields rather than pairwise gravity. Looks right, teaches right, runs fast. |
| VR/AR support | Immersive experience sounds amazing for space visualization | Massive scope increase. Requires stereoscopic rendering, head tracking, controller input redesign. Splits development focus. VR user base is small. Delays core product by months. | Build a great windowed 3D experience first. VR could be a future version if demand exists. The cinematic camera already provides an "immersive" guided experience. |
| Web-based deployment | "Share it easily" -- web apps have lower friction | WebGL/WebGPU cannot match desktop OpenGL 4.3 performance for 1M particles. Python backend would require full rewrite. Audio synthesis APIs are limited in browsers. Would compromise visual quality for accessibility. | Desktop application with video recording export for sharing. The MP4 output IS the shareable artifact. |
| User-defined custom simulations / sandbox mode | "Let me change the cosmological constant and see what happens" | Enormous complexity in physics validation. Every parameter change requires re-deriving era transitions, particle behaviors, visual mappings. Testing matrix explodes. Educational accuracy becomes impossible to guarantee. | Fixed simulation with scientifically accurate parameters. The guided experience IS the product. If users want sandboxes, Universe Sandbox exists. |
| Multiplayer / shared viewing | "Watch together with friends" | Network synchronization of particle state is a nightmare. Audio sync across network adds latency issues. Scope creep that serves a tiny use case. | Single-user experience. Share via recorded video or screenshots. |
| Realistic galaxy-scale rendering | "Show me the Milky Way forming in detail" | Rendering individual stars in a galaxy requires billions of particles or sophisticated LOD impostor systems. Way beyond scope. SpaceEngine spent years on this. | Represent galaxy formation as clustered particle groups with glow/nebula shaders. Suggestive rather than literal. Teaches the concept without requiring astronomical particle counts. |
| Mobile support | "I want it on my iPad" | Python + ModernGL is a desktop stack. Mobile would require complete rewrite in different technology. Touch controls are fundamentally different from mouse+keyboard. | Desktop only. Mobile users can watch exported videos. |
| Real-time parameter editing panel | "Let me tweak every physics constant live" | Exposes implementation details that confuse non-experts. Most parameter changes would break the simulation or produce nonsensical results. Testing every combination is impossible. | Expose only safe, meaningful controls: playback speed, camera position, HUD toggle, audio volume. The simulation parameters are the science -- they should be fixed and correct. |

## Feature Dependencies

```
[Core Rendering Engine (particles + shaders)]
    |-- requires --> [Window Management + OpenGL Context]
    |-- requires --> [Camera System]
    |-- enables --> [Post-Processing (bloom, tone mapping)]
    |-- enables --> [Screenshot Capture]
    |-- enables --> [Video Recording]

[Cosmological Physics Engine (era models + timeline)]
    |-- requires --> [Logarithmic Time Mapping]
    |-- enables --> [Per-Era Particle Behavior]
    |-- enables --> [Physics Readouts HUD]
    |-- enables --> [Era Labels + Timeline Bar]
    |-- enables --> [Milestone Markers]

[Per-Era Particle Behavior]
    |-- requires --> [Core Rendering Engine]
    |-- requires --> [Cosmological Physics Engine]
    |-- enables --> [Visually Distinct Eras]

[Visually Distinct Eras]
    |-- requires --> [Per-Era Particle Behavior]
    |-- requires --> [Post-Processing]
    |-- enables --> [Cinematic Auto-Camera]

[Cinematic Auto-Camera]
    |-- requires --> [Camera System]
    |-- requires --> [Visually Distinct Eras]
    |-- requires --> [Era Labels + Timeline Bar]
    |-- enables --> [Video Recording (full cinematic run)]

[Educational Overlays (HUD + explanations)]
    |-- requires --> [Era Labels + Timeline Bar]
    |-- requires --> [Physics Readouts HUD]
    |-- requires --> [Milestone Markers]

[Generative Ambient Soundscape]
    |-- requires --> [Cosmological Physics Engine (reads temperature, density, expansion rate)]
    |-- enhances --> [Cinematic Auto-Camera (audio completes the experience)]
    |-- enhances --> [Educational Overlays (audio cues at milestones)]

[Video Recording]
    |-- requires --> [Core Rendering Engine]
    |-- requires --> [Cinematic Auto-Camera (for full-run recording)]
    |-- enhances --> [Generative Ambient Soundscape (audio captured in video)]
```

### Dependency Notes

- **Core Rendering Engine requires Window Management:** OpenGL context must exist before any rendering. ModernGL needs a window with GL context (via pyglet, glfw, or SDL2).
- **Per-Era Particle Behavior requires both engines:** Particles need rendering (how they look) and physics (how they move). These two systems must be built in parallel or rendering first with placeholder physics.
- **Cinematic Auto-Camera requires Visually Distinct Eras:** Camera scripting is meaningless if every era looks the same. The camera path must be designed around visual landmarks.
- **Generative Soundscape requires Physics Engine:** Audio is driven by simulation state. Cannot be built in isolation -- needs live temperature, density, expansion rate feeds.
- **Video Recording requires Cinematic Camera:** Recording a manual camera session has limited value. The "full cinematic run" recording is the flagship output, requiring the auto-camera path.
- **Educational Overlays enhance but do not block the core:** The simulation can run without overlays. They should be toggleable (some users want pure visual immersion).

## MVP Definition

### Launch With (v1)

Minimum viable product -- what validates "cinematic Big Bang simulation" as a concept.

- [ ] **Core particle rendering engine** -- Instanced billboard particles with GLSL shaders, 100K+ particles at 30+ FPS. This is the foundation everything else sits on.
- [ ] **Window + camera system** -- Windowed/fullscreen OpenGL context with orbit/zoom/pan controls. Users must be able to see and navigate the simulation.
- [ ] **3-4 visually distinct eras** -- At minimum: early universe (hot plasma glow), recombination (CMB release, cooling), dark ages (dim neutral gas), first stars/galaxies (point lights forming clusters). Proves the timeline concept without requiring all 11 eras.
- [ ] **Basic timeline bar + era labels** -- Shows where you are in cosmic history. Logarithmic time mapping so early eras get screen time.
- [ ] **Play/pause/speed controls** -- Spacebar to pause, +/- to change speed. Non-negotiable for any simulation.
- [ ] **Post-processing (bloom + tone mapping)** -- Makes the difference between "tech demo" and "cinematic." Early universe must glow.
- [ ] **Screenshot capture** -- F12 to capture. Quick win that gives users shareable output immediately.

### Add After Validation (v1.x)

Features to add once the core rendering and timeline are working and visually compelling.

- [ ] **All 11 cosmological eras** -- Expand from 3-4 to the full set (Planck, GUT, Inflation, QGP, Hadron, Nucleosynthesis, Recombination, Dark Ages, Reionization, Galaxy Formation, Large-Scale Structure). Add when the per-era shader/physics pipeline is proven.
- [ ] **Cinematic auto-camera path** -- Scripted camera journey through the full timeline. Add when all eras are visually distinct and transition smoothly.
- [ ] **Physics readouts HUD** -- Temperature, density, scale factor readouts. Add when physics engine produces correct values for all eras.
- [ ] **Educational overlay text** -- Era descriptions, milestone markers, physics explanations. Add when the guided experience (auto-camera) works.
- [ ] **Generative ambient soundscape** -- Physics-driven audio. Add after the visual experience is solid -- audio enhances but should not block visual development.
- [ ] **Keyboard shortcuts** -- Full shortcut set beyond play/pause. Add as features accumulate.

### Future Consideration (v2+)

Features to defer until the core product is complete and validated.

- [ ] **Video recording (MP4 export)** -- Requires ffmpeg integration and frame-locked rendering. High value but significant complexity. Defer until cinematic auto-camera is polished.
- [ ] **High-resolution screenshot mode** -- Render at 2x or 4x display resolution for print-quality captures. Nice to have, not essential.
- [ ] **Configurable HUD density** -- Let users choose between minimal, standard, and detailed overlay modes. Defer until overlay content is finalized.
- [ ] **Accessibility features** -- Colorblind-safe palette options, high-contrast mode, keyboard-only navigation. Important but should be designed into v2 when UI patterns are stable.
- [ ] **Preset camera bookmarks** -- Save/load camera positions at interesting moments. Low priority nice-to-have.
- [ ] **Localization / multiple languages** -- Educational text in multiple languages. Defer until English content is finalized and validated.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Core particle rendering (instanced, GPU) | HIGH | HIGH | P1 |
| Window + OpenGL context + camera | HIGH | MEDIUM | P1 |
| Visually distinct eras (3-4 initial) | HIGH | HIGH | P1 |
| Play/pause/speed controls | HIGH | LOW | P1 |
| Timeline bar + era labels | HIGH | MEDIUM | P1 |
| Post-processing (bloom, tone mapping) | HIGH | MEDIUM | P1 |
| Screenshot capture | MEDIUM | LOW | P1 |
| All 11 cosmological eras | HIGH | HIGH | P2 |
| Cinematic auto-camera path | HIGH | MEDIUM | P2 |
| Physics readouts HUD | MEDIUM | MEDIUM | P2 |
| Educational overlay text | MEDIUM | MEDIUM | P2 |
| Generative ambient soundscape | HIGH | HIGH | P2 |
| Milestone markers | MEDIUM | LOW | P2 |
| Video recording (MP4) | MEDIUM | HIGH | P3 |
| Keyboard shortcuts (full set) | LOW | LOW | P2 |
| Accessibility features | MEDIUM | MEDIUM | P3 |
| High-res screenshot mode | LOW | LOW | P3 |
| Configurable HUD density | LOW | LOW | P3 |
| Localization | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch (validates the concept)
- P2: Should have, add once core works (completes the experience)
- P3: Nice to have, future consideration (polish and reach)

## Competitor Feature Analysis

| Feature | SpaceEngine | Universe Sandbox | Illustris TNG (web viewer) | NASA SVS (videos) | BigBangSim (our approach) |
|---------|-------------|------------------|---------------------------|-------------------|--------------------------|
| Real-time 3D rendering | Yes, photorealistic | Yes, functional | Web-based volume render | Pre-rendered video | Yes, GPU particle shaders |
| Big Bang timeline | No (present universe only) | No (sandbox, no timeline) | Yes (research data) | Yes (pre-rendered) | Yes, full 13.8 Gyr guided journey |
| Interactive camera | Full 6DOF | Full 6DOF | Limited web controls | None (fixed video) | Orbit/zoom/pan + cinematic auto |
| Educational overlays | Minimal labels | Some info panels | Research metadata | Narration in video | Rich contextual HUD with physics |
| Sonification/audio | Ambient music (not data-driven) | Sound effects | None | Separate sonification project | Generative physics-driven soundscape |
| Physics accuracy | Orbital mechanics | N-body gravity, collisions | Full magneto-hydrodynamics | Accurate visualizations | Friedmann, BBN, Saha, Jeans (simplified but correct) |
| Accessibility | Limited | Limited | None | Sonification project separate | Planned (colorblind, keyboard) |
| Video export | Yes (built-in) | External capture | None | N/A (is video) | Planned (MP4 via ffmpeg) |
| Platform | Windows/Linux | Windows/Mac/Linux | Web browser | Web (video) | Windows primary, cross-platform Python |
| Price | $25 (Steam) | $30 (Steam) | Free (research) | Free | Free / open source |
| Target audience | Space enthusiasts, filmmakers | Educators, gamers | Researchers | General public | Curious learners, educators, enthusiasts |

**Key gap BigBangSim fills:** No existing consumer product offers a guided, cinematic, interactive journey through the full Big Bang timeline with real-time rendering, educational context, and physics-driven audio. SpaceEngine explores the present. Universe Sandbox lets you play. Illustris is for researchers. NASA SVS produces pre-rendered videos. BigBangSim is the interactive documentary of cosmic history.

## Sources

- [SpaceEngine Camera Path Editor](https://steamcommunity.com/sharedfiles/filedetails/?id=3399427510) - Cinematic camera features
- [SpaceEngine Scenario Scripts](https://spaceengine.org/manual/making-addons/scenario-scripts/) - Scripted experiences
- [SpaceEngine vs Universe Sandbox discussion](https://www.quora.com/Outer-Space-How-is-SpaceEngine-different-from-Universe-Sandbox) - Feature comparison
- [CosmoVis Interactive Visualization](https://creativecodinglab.github.io/CosmoVis/) - Research-grade cosmology visualization
- [IllustrisTNG Project](https://www.tng-project.org/) - Galaxy formation simulation features
- [Illustris Media](https://www.illustris-project.org/media/) - Visualization outputs
- [NASA Universe of Sound (Chandra Sonification)](https://chandra.si.edu/sound/) - Data sonification approach
- [NASA Data Sonifications](https://www.nasa.gov/data-sonifications/) - Sonification methodology
- [PhET Interactive Simulations Research](https://phet.colorado.edu/en/research) - Educational simulation design principles
- [PhET Student Engagement Study](https://phet.colorado.edu/publications/MPTL_2010_PhET_final.pdf) - Minimal text, visual-first design
- [ModernGL Documentation](https://moderngl.readthedocs.io/en/latest/reference/compute_shader.html) - Compute shader support
- [ModernGL GitHub](https://github.com/moderngl/moderngl) - Instanced rendering capabilities
- [OpenGL Particle Instancing Tutorial](http://www.opengl-tutorial.org/intermediate-tutorials/billboards-particles/particles-instancing/) - Billboard particle technique
- [GPU Particle Simulation (Wicked Engine)](https://wickedengine.net/2017/11/gpu-based-particle-simulation/) - GPU particle architecture
- [Building a Million-Particle System (Gamasutra)](https://www.gamedeveloper.com/programming/building-a-million-particle-system) - Performance patterns
- [NVIDIA Volume Rendering Techniques (GPU Gems)](https://developer.nvidia.com/gpugems/gpugems/part-vi-beyond-triangles/chapter-39-volume-rendering-techniques) - Volumetric rendering
- [Nebula Rendering Techniques](https://tonisagrista.com/blog/2024/rendering-aurorae-nebulae/) - Volumetric nebula shaders
- [Cosmic Calendar (Berkeley)](https://evolution.berkeley.edu/chronozoom/CZ%20UCMP%20p.%204%20%20Big%20Bang%20and%20Cosmos%20%20Text%20Panel%200.pdf) - Logarithmic time scale for cosmic timeline
- [OpenSpace Project (GitHub)](https://github.com/OpenSpace/OpenSpace) - Open source astrovisualization
- [NASA SVS Big Bang Animation](https://svs.gsfc.nasa.gov/12656/) - Pre-rendered Big Bang visualization
- [CERN Big Bang Animation](https://home.cern/resources/video/physics/big-bang-animation) - Educational Big Bang content

---
*Feature research for: Cosmological Big Bang simulation visualization*
*Researched: 2026-03-27*
