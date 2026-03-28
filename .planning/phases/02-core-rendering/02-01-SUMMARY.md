---
phase: 02-core-rendering
plan: 01
subsystem: rendering
tags: [glsl, shaders, compute-shader, bloom, post-processing, shader-preprocessor, particle-system]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "OpenGL 4.3 window, camera system, GLSL 4.30 shader pattern, simulation state with PhysicsState"
provides:
  - "Python shader loader with #include preprocessing (load_shader_source)"
  - "3 shared GLSL include libraries: common.glsl, noise.glsl, colormap.glsl"
  - "Compute shader for GPU particle updates (particle_update.comp)"
  - "Particle vertex shader reading from SSBO (particle.vert)"
  - "2 per-era fragment shader variants: hot plasma (particle_hot.frag) and cool matter (particle_cool.frag)"
  - "4 post-processing shaders: fullscreen quad, bright extract, gaussian blur, tonemap"
affects: [02-core-rendering, 03-era-visuals]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Python-side shader #include preprocessor", "Per-era fragment shader variants (no mega-shader)", "std430 SSBO Particle struct layout (3x vec4)", "Ping-pong compute shader pattern", "5-pass bloom chain (bright extract, 2x blur, composite + tonemap)"]

key-files:
  created:
    - bigbangsim/rendering/shader_loader.py
    - bigbangsim/shaders/include/common.glsl
    - bigbangsim/shaders/include/noise.glsl
    - bigbangsim/shaders/include/colormap.glsl
    - bigbangsim/shaders/compute/particle_update.comp
    - bigbangsim/shaders/vertex/particle.vert
    - bigbangsim/shaders/fragment/particle_hot.frag
    - bigbangsim/shaders/fragment/particle_cool.frag
    - bigbangsim/shaders/postprocess/fullscreen.vert
    - bigbangsim/shaders/postprocess/bright_extract.frag
    - bigbangsim/shaders/postprocess/gaussian_blur.frag
    - bigbangsim/shaders/postprocess/tonemap.frag
    - tests/test_shader_loader.py
  modified: []

key-decisions:
  - "Single-level include resolution only (no recursion) for simplicity and predictability"
  - "Particle struct uses 3x vec4 layout for std430 alignment safety (position+life, velocity+type, color)"
  - "Ashima Arts public-domain simplex noise for GLSL noise generation"
  - "Simplified Planckian locus approximation for temperature-to-color mapping (4 temperature bands)"

patterns-established:
  - "Shader include: use #include \"filename.glsl\" resolved by shader_loader.py from shaders/include/"
  - "Shader organization: compute/, vertex/, fragment/, postprocess/ subdirs under shaders/"
  - "Per-era shading: separate fragment shader programs per visual style, no if/else branching on era index"
  - "SSBO particle layout: struct Particle { vec4 position, vec4 velocity, vec4 color } with std430"
  - "Post-processing: fullscreen.vert + specialized fragment shader pattern for each pass"

requirements-completed: [RNDR-06]

# Metrics
duration: 5min
completed: 2026-03-28
---

# Phase 2 Plan 01: Shader Infrastructure Summary

**Modular per-era GLSL shader architecture with Python include preprocessor, 11 GPU shader files, and 6 unit tests**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-28T19:39:58Z
- **Completed:** 2026-03-28T19:45:01Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- Python shader loader (`shader_loader.py`) with regex-based `#include` directive preprocessing, single-level resolution, and descriptive error messages
- 3 shared GLSL include libraries: common uniforms/Particle struct, 2D simplex noise (Ashima Arts), and temperature/density color mapping
- Complete per-era shader set: compute shader for particle physics updates, vertex shader reading from SSBO, 2 distinct fragment variants (hot plasma vs cool matter) proving no mega-shader architecture (RNDR-06)
- 4 post-processing shaders: fullscreen quad passthrough, bloom bright-pass extraction, separable 5-tap Gaussian blur, HDR tone mapping with bloom composite
- 6 unit tests covering all shader_loader behaviors: passthrough, single include, no nesting, missing file error, multiple includes, get_shader_dir

## Task Commits

Each task was committed atomically:

1. **Task 1: Shader loader with include preprocessing and unit tests** - `bd26901` (feat, TDD)
2. **Task 2: All GLSL shader files** - `7a695f5` (feat)

## Files Created/Modified
- `bigbangsim/rendering/shader_loader.py` - Python shader include preprocessor with load_shader_source() and get_shader_dir()
- `bigbangsim/shaders/include/common.glsl` - Shared uniform declarations and Particle struct for SSBO layout
- `bigbangsim/shaders/include/noise.glsl` - 2D simplex noise (Ashima Arts, public domain)
- `bigbangsim/shaders/include/colormap.glsl` - Temperature-to-RGB blackbody approximation and density-to-color mapping
- `bigbangsim/shaders/compute/particle_update.comp` - Compute shader: Hubble expansion, damping, position integration, particle aging
- `bigbangsim/shaders/vertex/particle.vert` - Vertex shader reading particle data from SSBO via gl_VertexID, point size scaling
- `bigbangsim/shaders/fragment/particle_hot.frag` - Early-era fragment: temperature-based coloring with soft circular particles and glow
- `bigbangsim/shaders/fragment/particle_cool.frag` - Late-era fragment: density-based coloring with sharper falloff
- `bigbangsim/shaders/postprocess/fullscreen.vert` - Fullscreen quad passthrough matching geometry.quad_fs() attributes
- `bigbangsim/shaders/postprocess/bright_extract.frag` - Bloom bright-pass with luminance threshold
- `bigbangsim/shaders/postprocess/gaussian_blur.frag` - Separable 5-tap Gaussian blur (horizontal/vertical toggle)
- `bigbangsim/shaders/postprocess/tonemap.frag` - HDR tone mapping (exposure-based Reinhard) with bloom composite and gamma correction
- `tests/test_shader_loader.py` - 6 unit tests for shader loader include preprocessing

## Decisions Made
- Single-level include resolution only (no recursion): keeps the preprocessor simple and predictable; deeply nested includes are an anti-pattern for GLSL organization
- Particle struct uses 3x vec4 (position+life, velocity+type, color): ensures safe std430 alignment and avoids vec3 padding issues in SSBOs
- Simplified 4-band Planckian locus for temperature_to_color: good visual approximation without expensive spectral integration, suitable for real-time rendering
- Ashima Arts simplex noise (public domain): well-tested GLSL implementation, standard in graphics community

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed #include text from common.glsl comment**
- **Found during:** Task 2 verification
- **Issue:** A comment in common.glsl contained the literal text `#include "common.glsl"` which caused the verification assertion `'#include' not in src` to fail after include resolution (the comment was inlined into consuming shaders)
- **Fix:** Changed comment from `via #include "common.glsl"` to `via include directive`
- **Files modified:** bigbangsim/shaders/include/common.glsl
- **Verification:** All shader load assertions pass cleanly
- **Committed in:** 7a695f5 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Trivial comment fix. No scope creep.

## Issues Encountered
None beyond the comment text issue documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All shader source files are ready for Plan 02 (ParticleSystem and PostProcessingPipeline Python classes) to compile via `ctx.program()` and `ctx.compute_shader()`
- shader_loader.py provides the include preprocessing that Plan 02's Python classes will call
- SSBO Particle struct layout is established for Plan 02's buffer initialization
- Post-processing shaders are ready for the FBO chain in Plan 02's PostProcessingPipeline

## Self-Check: PASSED

All 13 created files verified present. Both task commits (bd26901, 7a695f5) verified in git log.

---
*Phase: 02-core-rendering*
*Completed: 2026-03-28*
