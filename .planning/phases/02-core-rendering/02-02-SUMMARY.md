---
phase: 02-core-rendering
plan: 02
subsystem: rendering
tags: [moderngl, ssbo, compute-shader, ping-pong, hdr, bloom, tone-mapping, glsl, particles, postprocessing]

# Dependency graph
requires:
  - phase: 02-core-rendering/01
    provides: "shader_loader.py (load_shader_source), all GLSL shader files"
provides:
  - "ParticleSystem class with ping-pong SSBOs and compute dispatch"
  - "PostProcessingPipeline class with HDR FBO and 5-pass bloom chain"
  - "PARTICLE_STRIDE constant (48 bytes per particle)"
  - "Era-based shader switching (hot/cool variants)"
affects: [02-core-rendering/03, 03-era-visuals]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ping-pong double buffering for GPU particle updates"
    - "Half-resolution bloom for performance"
    - "Mock-based GPU testing (no real OpenGL context required)"
    - "TDD for rendering classes (RED-GREEN with mock contexts)"

key-files:
  created:
    - bigbangsim/rendering/particles.py
    - bigbangsim/rendering/postprocessing.py
    - tests/test_particles.py
    - tests/test_postprocessing.py
  modified: []

key-decisions:
  - "Mock-based testing strategy: all 37 tests run without GPU via MagicMock context"
  - "Empty VAO for gl_VertexID-based particle rendering (no vertex attributes)"
  - "6 blur iterations (3H + 3V) as default for smooth bloom spread"

patterns-established:
  - "GPU resource classes follow init/update/render/release lifecycle"
  - "Static _generate_initial_particles for testable CPU-side data generation"
  - "begin_scene/end_scene pattern for post-processing pipeline integration"

requirements-completed: [RNDR-01, RNDR-02]

# Metrics
duration: 5min
completed: 2026-03-28
---

# Phase 02 Plan 02: Particle System and Post-Processing Summary

**Ping-pong double-buffered ParticleSystem with compute dispatch and HDR bloom pipeline with half-res Gaussian blur and Reinhard tone mapping**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-28T19:48:25Z
- **Completed:** 2026-03-28T19:53:17Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- ParticleSystem with ping-pong SSBOs (48-byte stride), compute dispatch with ceiling division and memory barrier, era-based hot/cool shader switching
- PostProcessingPipeline with RGBA16F HDR FBO, half-resolution bloom extraction, 6-iteration ping-pong Gaussian blur, Reinhard tone mapping with configurable exposure/bloom_strength
- 37 new tests (19 particles + 18 postprocessing) all passing without GPU, full suite at 130 tests green

## Task Commits

Each task was committed atomically:

1. **Task 1: ParticleSystem class with ping-pong SSBOs and compute dispatch**
   - `f2300ce` (test: failing tests for ParticleSystem -- RED)
   - `c3134bd` (feat: implement ParticleSystem -- GREEN)
2. **Task 2: PostProcessingPipeline class with HDR FBO and bloom chain**
   - `7f7abdc` (test: failing tests for PostProcessingPipeline -- RED)
   - `c46fc94` (feat: implement PostProcessingPipeline -- GREEN)

_TDD pattern: RED (failing tests) -> GREEN (implementation passes) for both tasks_

## Files Created/Modified
- `bigbangsim/rendering/particles.py` - GPU particle system with ping-pong SSBOs, compute dispatch, era-based shader switching
- `bigbangsim/rendering/postprocessing.py` - HDR FBO, bloom extraction, Gaussian blur, tone mapping pipeline
- `tests/test_particles.py` - 19 tests: data generation, buffer logic, shader selection
- `tests/test_postprocessing.py` - 18 tests: defaults, dimensions, methods, shader loading

## Decisions Made
- Mock-based testing strategy: all rendering tests use MagicMock for moderngl.Context, enabling CI without GPU
- Empty VAO approach for gl_VertexID rendering: particles have no vertex attributes, data comes from SSBO
- 6 blur iterations default (3 horizontal + 3 vertical) balances visual quality with performance

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - all classes are fully implemented with real logic, no placeholder data.

## Next Phase Readiness
- ParticleSystem and PostProcessingPipeline ready for app integration in Plan 03
- Both classes use shader_loader for all GLSL loading (established in Plan 01)
- Pipeline follows begin_scene/end_scene pattern for easy render loop integration

## Self-Check: PASSED

- All 4 created files exist on disk
- All 4 commits (f2300ce, c3134bd, 7f7abdc, c46fc94) found in git history
- 130 tests passing (full suite)
- Both classes importable without errors

---
*Phase: 02-core-rendering*
*Completed: 2026-03-28*
