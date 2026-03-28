# Requirements: BigBangSim

**Defined:** 2026-03-27
**Core Value:** The simulation must be both scientifically accurate AND visually stunning — real cosmological physics driving beautiful real-time 3D rendering that teaches as it mesmerizes.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Rendering

- [ ] **RNDR-01**: Application renders 100K-1M particles in real-time via GPU compute shaders at 30+ FPS
- [ ] **RNDR-02**: Post-processing pipeline applies bloom, HDR, and tone mapping to produce cinematic glow effects
- [ ] **RNDR-03**: Each of the 11 cosmological eras has visually distinct shader programs with unique color palettes and particle behaviors
- [ ] **RNDR-04**: Era transitions crossfade smoothly between visual paradigms (no jarring cuts)
- [ ] **RNDR-05**: Application supports fullscreen toggle and remembers window state
- [ ] **RNDR-06**: Per-era shader architecture uses shared utility libraries with separate programs per era (not a mega-shader)

### Camera

- [ ] **CAMR-01**: User can orbit, zoom, and pan the camera with smooth damping via mouse controls
- [ ] **CAMR-02**: Cinematic auto-camera follows a scripted path through all 11 eras with smooth transitions
- [ ] **CAMR-03**: User can pause auto-camera at any time and freely orbit/zoom, then resume cinematic mode
- [ ] **CAMR-04**: Play/pause via spacebar, speed controls via +/- keys (0.5x to 10x range)

### Physics & Simulation

- [ ] **PHYS-01**: Simulation covers all 11 cosmological eras: Planck epoch, Grand Unification, Inflation, Quark-Gluon Plasma, Hadron epoch, Nucleosynthesis, Recombination/CMB, Dark Ages, Reionization/First Stars, Galaxy Formation, Large-Scale Structure
- [ ] **PHYS-02**: Each era uses real cosmological physics models — Friedmann equations for expansion, BBN yields for nucleosynthesis, Saha equation for recombination, Jeans instability for structure formation, Press-Schechter for halo statistics
- [ ] **PHYS-03**: Logarithmic time mapping spans 60+ orders of magnitude (10^-43 seconds to 13.8 billion years) with intuitive visual timeline bar
- [ ] **PHYS-04**: ~20 milestone markers trigger at correct cosmic timestamps ("First protons form", "Universe becomes transparent", "First stars ignite", etc.)
- [ ] **PHYS-05**: All physics constants sourced from Planck 2018 results and PDG values — centralized constants module with citations
- [ ] **PHYS-06**: Fixed-timestep simulation decoupled from render rate with interpolation for smooth display
- [ ] **PHYS-07**: Camera-relative rendering and era-specific coordinate systems to avoid floating-point precision breakdown at cosmic scales

### Educational HUD

- [ ] **HUD-01**: Current era name displayed prominently with visual timeline bar showing position across all eras
- [ ] **HUD-02**: Live physics readouts showing cosmic temperature, matter density, radiation density, and scale factor a(t)
- [ ] **HUD-03**: Contextual educational explanations appear at key moments describing what is happening and why
- [ ] **HUD-04**: HUD uses imgui-bundle for overlay rendering with clean, non-intrusive design following PhET minimal-text principles
- [ ] **HUD-05**: HUD elements can be toggled on/off by the user

### Output & Capture

- [ ] **CAPT-01**: User can capture high-resolution screenshots at any moment via keypress (PNG format)
- [ ] **CAPT-02**: Full cinematic run can be recorded to MP4 via ffmpeg subprocess with frame-locked capture for consistent quality
- [ ] **CAPT-03**: Video recording decoupled from real-time playback (frame-locked) so output quality is independent of GPU speed

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Audio

- **AUDIO-01**: Generative ambient soundscape driven by physics parameters (temperature to pitch, density to texture)
- **AUDIO-02**: Each era has a distinct sonic character that evolves continuously with simulation state
- **AUDIO-03**: Audio cues trigger at milestone markers for emphasis
- **AUDIO-04**: Volume controls and mute toggle

### Controls

- **CTRL-01**: Full keyboard shortcut documentation accessible in-app
- **CTRL-02**: Parameter presets for different universe configurations

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Full N-body gravity simulation | Computationally intractable at cosmological scale on consumer GPU. Use approximate methods (Jeans instability, Press-Schechter) instead. |
| VR/AR support | Massive scope increase requiring stereoscopic rendering, head tracking, controller redesign. Build great windowed 3D first. |
| Web-based deployment | WebGL/WebGPU cannot match desktop OpenGL 4.3 for 1M particles. Audio synthesis limited in browsers. MP4 export is the shareable artifact. |
| Sandbox mode / parameter editing | Every parameter change requires re-deriving era transitions. Testing matrix explodes. Educational accuracy impossible to guarantee. |
| Mobile support | Python + ModernGL is desktop stack. Mobile requires complete rewrite. |
| Multiplayer / shared viewing | Network sync of particle state is a nightmare. Share via recorded video instead. |
| Realistic galaxy-scale rendering | Requires billions of particles or sophisticated LOD. Represent galaxies as clustered particle groups with glow shaders. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| RNDR-01 | TBD | Pending |
| RNDR-02 | TBD | Pending |
| RNDR-03 | TBD | Pending |
| RNDR-04 | TBD | Pending |
| RNDR-05 | TBD | Pending |
| RNDR-06 | TBD | Pending |
| CAMR-01 | TBD | Pending |
| CAMR-02 | TBD | Pending |
| CAMR-03 | TBD | Pending |
| CAMR-04 | TBD | Pending |
| PHYS-01 | TBD | Pending |
| PHYS-02 | TBD | Pending |
| PHYS-03 | TBD | Pending |
| PHYS-04 | TBD | Pending |
| PHYS-05 | TBD | Pending |
| PHYS-06 | TBD | Pending |
| PHYS-07 | TBD | Pending |
| HUD-01 | TBD | Pending |
| HUD-02 | TBD | Pending |
| HUD-03 | TBD | Pending |
| HUD-04 | TBD | Pending |
| HUD-05 | TBD | Pending |
| CAPT-01 | TBD | Pending |
| CAPT-02 | TBD | Pending |
| CAPT-03 | TBD | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 0
- Unmapped: 25

---
*Requirements defined: 2026-03-27*
*Last updated: 2026-03-27 after initial definition*
