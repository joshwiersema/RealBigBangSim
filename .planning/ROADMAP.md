# Roadmap: BigBangSim

## Overview

BigBangSim delivers a cinematic, scientifically accurate Big Bang simulation in five phases. We start by building the invisible foundations that everything depends on -- the physics engine, timeline controller, and camera system. Then we add GPU-accelerated particle rendering with a modular shader architecture. With the rendering pipeline proven, we populate all 11 cosmological eras with real physics models and smooth transitions. Next comes the presentation layer: educational HUD, cinematic auto-camera, and milestone markers. Finally, we add screenshot/video capture and polish the experience for delivery.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Physics engine, timeline controller, camera controls, and cosmological constants module
- [ ] **Phase 2: Core Rendering** - GPU particle system with compute shaders, shader architecture, and post-processing pipeline
- [ ] **Phase 3: Era Content** - All 11 cosmological eras with physics models, distinct visuals, and smooth transitions
- [ ] **Phase 4: Presentation** - Educational HUD overlays, cinematic auto-camera, and milestone markers
- [ ] **Phase 5: Capture & Polish** - Screenshot capture, video recording, fullscreen toggle, and final integration

## Phase Details

### Phase 1: Foundation
**Goal**: Users can launch the application and see a working 3D window with camera controls, while the physics engine accurately computes cosmological parameters across the full 13.8-billion-year timeline
**Depends on**: Nothing (first phase)
**Requirements**: CAMR-01, CAMR-04, PHYS-03, PHYS-05, PHYS-06, PHYS-07
**Success Criteria** (what must be TRUE):
  1. User can launch the application and see a 3D OpenGL window with a visible test scene
  2. User can orbit, zoom, and pan the camera with smooth damping using mouse controls
  3. User can press spacebar to play/pause and +/- to change simulation speed (0.5x-10x)
  4. A visual timeline bar shows the current cosmic time position across 60+ orders of magnitude with per-era time budgets
  5. All cosmological constants are sourced from Planck 2018 / PDG values with citation comments in a centralized module
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md -- Project scaffolding, cosmological constants module (Planck 2018/PDG), PhysicsState dataclass
- [x] 01-02-PLAN.md -- Piecewise logarithmic timeline controller, Friedmann cosmology solver, fixed-timestep simulation engine
- [ ] 01-03-PLAN.md -- OpenGL window, damped orbit camera, play/pause/speed controls, timeline bar, test scene

### Phase 2: Core Rendering
**Goal**: The simulation renders 100K+ particles in real-time via GPU compute shaders with cinematic post-processing effects, proving the rendering architecture before era content is added
**Depends on**: Phase 1
**Requirements**: RNDR-01, RNDR-02, RNDR-06
**Success Criteria** (what must be TRUE):
  1. Application renders 100K-1M particles at 30+ FPS on a GTX 1060-class GPU using compute shader updates
  2. Bloom, HDR, and tone mapping produce visible cinematic glow effects on the particle scene
  3. Shader architecture uses shared utility libraries with separate per-era shader programs (not a mega-shader), verified by at least 2 distinct shader variants loading successfully
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

### Phase 3: Era Content
**Goal**: Users experience a complete journey through all 11 cosmological eras, each with scientifically accurate physics and visually distinct rendering, connected by smooth transitions
**Depends on**: Phase 2
**Requirements**: RNDR-03, RNDR-04, PHYS-01, PHYS-02
**Success Criteria** (what must be TRUE):
  1. All 11 cosmological eras (Planck epoch through Large-Scale Structure) are present and play in correct sequence during a full timeline run
  2. Each era is visually distinct with unique color palettes and particle behaviors driven by its physics model (Friedmann equations, BBN yields, Saha equation, Jeans instability, Press-Schechter)
  3. Era transitions crossfade smoothly between visual paradigms with no jarring cuts or discontinuities
  4. A full timeline playthrough from singularity to large-scale structure completes without crashes or visual artifacts
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

### Phase 4: Presentation
**Goal**: Users receive a guided, educational experience with rich HUD overlays explaining the physics, a cinematic auto-camera that navigates the journey, and milestone markers at key cosmic moments
**Depends on**: Phase 3
**Requirements**: CAMR-02, CAMR-03, PHYS-04, HUD-01, HUD-02, HUD-03, HUD-04, HUD-05
**Success Criteria** (what must be TRUE):
  1. Current era name and a visual timeline bar are displayed prominently showing position across all eras
  2. Live physics readouts (temperature, density, radiation density, scale factor) update in real-time as the simulation progresses
  3. Contextual educational explanations appear at key moments describing what is happening and why
  4. Approximately 20 milestone markers trigger at correct cosmic timestamps with visible notifications
  5. Cinematic auto-camera follows scripted paths through all 11 eras, and user can pause it to freely orbit/zoom, then resume
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

### Phase 5: Capture & Polish
**Goal**: Users can capture and share the experience through high-resolution screenshots and full cinematic video recording, with final polish for a complete desktop application
**Depends on**: Phase 4
**Requirements**: RNDR-05, CAPT-01, CAPT-02, CAPT-03
**Success Criteria** (what must be TRUE):
  1. User can press a key to capture a high-resolution PNG screenshot at any moment during the simulation
  2. User can record a full cinematic run to MP4 via ffmpeg with consistent quality independent of GPU speed (frame-locked capture)
  3. Application supports fullscreen toggle and remembers window state between sessions
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/3 | Planning complete | - |
| 2. Core Rendering | 0/0 | Not started | - |
| 3. Era Content | 0/0 | Not started | - |
| 4. Presentation | 0/0 | Not started | - |
| 5. Capture & Polish | 0/0 | Not started | - |
