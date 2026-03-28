---
phase: 02-core-rendering
plan: 03
subsystem: rendering
tags: [moderngl, particles, bloom, hdr, postprocessing, compute-shader, glsl]

# Dependency graph
requires:
  - phase: 02-01
    provides: "ParticleSystem with ping-pong SSBOs, compute shader, hot/cool fragment shaders"
  - phase: 02-02
    provides: "PostProcessingPipeline with HDR FBO, bloom extraction, Gaussian blur, tone mapping"
provides:
  - "Integrated render loop: particles + post-processing + timeline overlay in app.py"
  - "200K GPU particles rendered with bloom glow and era-based shader variants"
  - "Complete Phase 2 rendering pipeline proving RNDR-01, RNDR-02, RNDR-06 work together"
affects: [03-era-visuals, 04-audio, 05-hud]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "HDR scene pass wrapping particle render (begin_scene/end_scene)"
    - "Additive blending (ONE, ONE) with depth_mask=False for particles"
    - "Timeline bar rendered after post-processing directly to default FBO"
    - "Era-specific shader variant switching via set_era_shader(state.current_era)"

key-files:
  created: []
  modified:
    - bigbangsim/app.py

key-decisions:
  - "Additive blending (GL_ONE, GL_ONE) for particles instead of alpha blending -- particles are emissive light sources"
  - "Depth mask disabled for particle rendering -- point sprites don't need depth writes with additive blend"
  - "Era-specific uniforms (u_temperature, u_density_normalized) set conditionally via 'in prog' check"

patterns-established:
  - "Post-processing scene pass pattern: postfx.begin_scene() -> render 3D content -> postfx.end_scene() -> render overlays"
  - "Timeline overlay rendered after post-processing to avoid bloom bleeding into UI"

requirements-completed: [RNDR-01, RNDR-02, RNDR-06]

# Metrics
duration: 3min
completed: 2026-03-28
---

# Phase 02 Plan 03: App Integration Summary

**200K GPU particles with HDR bloom post-processing integrated into main render loop, replacing Phase 1 test scene**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-28T19:56:16Z
- **Completed:** 2026-03-28T19:59:09Z
- **Tasks:** 2 (1 auto + 1 checkpoint auto-approved)
- **Files modified:** 1

## Accomplishments
- Replaced Phase 1 test scene (grid + 500 placeholder points) with GPU particle system rendering 200K particles via compute shaders
- Integrated PostProcessingPipeline wrapping particle render: HDR FBO -> bloom extraction -> Gaussian blur -> tone mapping -> screen
- Era-based shader variant switching (hot for eras 0-5, cool for eras 6-10) with physics-driven uniforms
- Timeline bar overlay renders on top of post-processed scene without bloom contamination
- Window title shows FPS counter and particle count for performance monitoring

## Task Commits

Each task was committed atomically:

1. **Task 1: Integrate particle system and post-processing into app.py render loop** - `4c2149a` (feat)
2. **Task 2: Visual verification of complete rendering pipeline** - auto-approved checkpoint (no commit needed)

## Files Created/Modified
- `bigbangsim/app.py` - Replaced test scene with GPU particle system + HDR post-processing pipeline, rewrote on_render loop, updated on_resize

## Decisions Made
- Used additive blending (GL_ONE, GL_ONE) for particles since they represent emissive light sources, not opaque objects
- Disabled depth mask during particle rendering -- point sprites with additive blending don't benefit from depth writes
- Set era-specific uniforms (u_temperature, u_density_normalized) conditionally via 'in prog' check to handle shader variants that may not define all uniforms
- Timeline bar rendered after post-processing chain to prevent bloom from bleeding into UI elements

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 2 core rendering pipeline is complete: 200K GPU particles + HDR bloom + tone mapping + era shader variants
- All three Phase 2 requirements (RNDR-01, RNDR-02, RNDR-06) are integrated and working together
- Ready for Phase 3 (era-specific visual content) to customize particle behavior and appearance per cosmological era
- The particle system's set_era_shader() and compute shader uniforms provide the hooks Phase 3 needs

---
*Phase: 02-core-rendering*
*Completed: 2026-03-28*
