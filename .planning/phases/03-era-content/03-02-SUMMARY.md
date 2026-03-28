---
phase: 03-era-content
plan: 02
subsystem: rendering
tags: [glsl, shaders, fragment-shaders, compute-shader, simplex-noise, crossfade, era-visuals]

# Dependency graph
requires:
  - phase: 02-core-rendering
    provides: shader_loader with include resolution, particle system SSBO, postprocess pipeline
provides:
  - 11 per-era fragment shaders (era_00 through era_10) with distinct visual identities
  - Uniform-driven compute shader with per-era expansion/noise/gravity/damping
  - 3D simplex noise (snoise3) in noise.glsl for volumetric turbulence
  - era_utils.glsl with soft_glow, sharp_glow, smoothstep_ease utilities
  - era_crossfade.frag for FBO-based era transition blending
  - u_point_scale_era in vertex shader for per-era particle sizing
affects: [03-era-content, 04-audio, rendering-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: [per-era uniform scoping to avoid GLSL optimization KeyError, Ashima Arts webgl-noise 3D variant]

key-files:
  created:
    - bigbangsim/shaders/include/era_utils.glsl
    - bigbangsim/shaders/postprocess/era_crossfade.frag
    - bigbangsim/shaders/fragment/era_00_planck.frag
    - bigbangsim/shaders/fragment/era_01_gut.frag
    - bigbangsim/shaders/fragment/era_02_inflation.frag
    - bigbangsim/shaders/fragment/era_03_qgp.frag
    - bigbangsim/shaders/fragment/era_04_hadron.frag
    - bigbangsim/shaders/fragment/era_05_nucleosynthesis.frag
    - bigbangsim/shaders/fragment/era_06_recombination.frag
    - bigbangsim/shaders/fragment/era_07_dark_ages.frag
    - bigbangsim/shaders/fragment/era_08_first_stars.frag
    - bigbangsim/shaders/fragment/era_09_galaxy_formation.frag
    - bigbangsim/shaders/fragment/era_10_lss.frag
    - tests/test_era_shaders.py
  modified:
    - bigbangsim/shaders/include/noise.glsl
    - bigbangsim/shaders/include/common.glsl
    - bigbangsim/shaders/compute/particle_update.comp
    - bigbangsim/shaders/vertex/particle.vert

key-decisions:
  - "Physics-specific uniforms scoped per-shader to avoid GLSL optimization removing unused uniforms (Phase 2 pitfall c94d2c1)"
  - "Compute shader uses uniform-driven behavior instead of hardcoded constants for per-era physics"

patterns-established:
  - "Per-era fragment shader naming: era_XX_name.frag with common include pattern"
  - "Uniform scoping: common uniforms in common.glsl, physics-specific uniforms only in shaders that use them"
  - "Glow patterns: soft_glow for diffuse/energy, sharp_glow for discrete particles"

requirements-completed: [RNDR-03, RNDR-04]

# Metrics
duration: 4min
completed: 2026-03-28
---

# Phase 3 Plan 02: Era Shaders Summary

**11 per-era GLSL fragment shaders with uniform-driven compute physics, 3D simplex noise, and FBO crossfade compositor**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-28T20:29:57Z
- **Completed:** 2026-03-28T20:34:51Z
- **Tasks:** 2
- **Files modified:** 18

## Accomplishments
- Created all 11 per-era fragment shaders (Planck through Large-Scale Structure), each with visually distinct rendering: noise-driven energy fields, fluid turbulence, ionization-fraction opacity, bimodal star/gas brightness, density-mapped clustering
- Upgraded compute shader from hardcoded expansion to uniform-driven per-era behavior (u_expansion_rate, u_noise_strength, u_gravity_strength, u_damping) with 3D simplex noise turbulence
- Built shared GLSL utilities: 3D simplex noise (snoise3) from Ashima Arts, era_utils.glsl with soft_glow/sharp_glow point sprite functions, crossfade compositor for FBO-based era transitions
- Added 94 tests validating shader structure, uniform scoping, include resolution, and physics-specific uniform isolation

## Task Commits

Each task was committed atomically:

1. **Task 1: GLSL utility upgrades** - `5c64a00` (feat)
2. **Task 2: All 11 per-era fragment shaders** - `2e9ef5b` (feat)

## Files Created/Modified
- `bigbangsim/shaders/include/noise.glsl` - Added 3D simplex noise (snoise3) below existing 2D code
- `bigbangsim/shaders/include/era_utils.glsl` - New shared era utility functions (soft_glow, sharp_glow, smoothstep_ease)
- `bigbangsim/shaders/include/common.glsl` - Added per-era behavior uniforms (expansion, noise, gravity, damping)
- `bigbangsim/shaders/vertex/particle.vert` - Added u_point_scale_era for per-era particle sizing
- `bigbangsim/shaders/compute/particle_update.comp` - Full upgrade to uniform-driven per-era physics with 3D noise
- `bigbangsim/shaders/postprocess/era_crossfade.frag` - FBO crossfade composite for era transitions
- `bigbangsim/shaders/fragment/era_00_planck.frag` - Blinding white energy glow with high-frequency noise
- `bigbangsim/shaders/fragment/era_01_gut.frag` - Warm gold to cool lavender with slow noise animation
- `bigbangsim/shaders/fragment/era_02_inflation.frag` - Bright yellow-white with elongated motion blur
- `bigbangsim/shaders/fragment/era_03_qgp.frag` - Deep orange-red fluid with temperature-driven turbulence
- `bigbangsim/shaders/fragment/era_04_hadron.frag` - Orange-amber with sharp edges (discrete particle formation)
- `bigbangsim/shaders/fragment/era_05_nucleosynthesis.frag` - Green-gold with helium fraction driven coloring
- `bigbangsim/shaders/fragment/era_06_recombination.frag` - Dramatic plasma-to-transparent opacity via ionization fraction
- `bigbangsim/shaders/fragment/era_07_dark_ages.frag` - Near-black with faint blue density perturbations
- `bigbangsim/shaders/fragment/era_08_first_stars.frag` - Bimodal: dim gas vs bright blue-white stars
- `bigbangsim/shaders/fragment/era_09_galaxy_formation.frag` - Density-mapped clustering with collapsed fraction
- `bigbangsim/shaders/fragment/era_10_lss.frag` - Mature cosmic web with golden-white cluster highlights
- `tests/test_era_shaders.py` - 94 tests for shader validation

## Decisions Made
- Physics-specific uniforms (u_ionization_fraction, u_helium_fraction, u_reionization_frac, u_collapsed_fraction) scoped to only the shaders that use them, preventing GLSL optimization KeyError from Phase 2 pitfall (c94d2c1)
- Compute shader uses uniform-driven behavior (u_expansion_rate, u_noise_strength, u_gravity_strength, u_damping) rather than hardcoded constants, enabling EraVisualConfig from Plan 01 to control per-era physics

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - all shaders are fully implemented with real logic, no placeholder data.

## Next Phase Readiness
- All 11 per-era fragment shaders ready for Python-side EraVisualConfig (Plan 01) to drive via uniforms
- Compute shader ready for per-era physics tuning via uniform uploads
- Crossfade shader ready for era transition system (Plan 03)
- 224 tests passing (130 existing + 94 new)

## Self-Check: PASSED

All 18 created/modified files verified on disk. Both task commits (5c64a00, 2e9ef5b) verified in git log.

---
*Phase: 03-era-content*
*Completed: 2026-03-28*
